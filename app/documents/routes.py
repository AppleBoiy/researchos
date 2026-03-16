import mimetypes
import os
import uuid

from flask import request, current_app, send_file
from flask_restx import Namespace, Resource, fields
from flask_security import auth_required, current_user

from app.extensions import db, api
from app.models import Document, DocumentTag, Tag

documents_ns = Namespace("documents", description="Document management")

VALID_FILE_TYPES = {"pdf", "latex", "dataset", "other"}

# --- Swagger models ---

_tag_model = documents_ns.model("Tag", {
    "id": fields.String(description="Tag UUID"),
    "name": fields.String(description="Tag name"),
    "accepted": fields.Boolean(description="Whether the tag is accepted"),
})

_document_model = documents_ns.model("Document", {
    "id": fields.String(description="Document UUID"),
    "title": fields.String(description="Document title"),
    "description": fields.String(description="Optional description"),
    "file_type": fields.String(description="One of: pdf, latex, dataset, other"),
    "file_size": fields.Integer(description="File size in bytes"),
    "category": fields.String(description="Optional category"),
    "tags": fields.List(fields.Nested(_tag_model)),
    "created_at": fields.String(description="ISO8601 timestamp"),
    "updated_at": fields.String(description="ISO8601 timestamp"),
})

_document_list_model = documents_ns.model("DocumentList", {
    "items": fields.List(fields.Nested(_document_model)),
    "total": fields.Integer,
    "page": fields.Integer,
    "per_page": fields.Integer,
    "pages": fields.Integer,
})

# Upload form parser (multipart/form-data)
_upload_parser = documents_ns.parser()
_upload_parser.add_argument("title", location="form", required=True, help="Document title")
_upload_parser.add_argument(
    "file_type", location="form", required=True,
    help="One of: pdf, latex, dataset, other",
    choices=("pdf", "latex", "dataset", "other"),
)
_upload_parser.add_argument("description", location="form", required=False, help="Optional description")
_upload_parser.add_argument("category", location="form", required=False, help="Optional category")
_upload_parser.add_argument("file", location="files", required=True, type="FileStorage", help="File to upload")

# List query parser
_list_parser = documents_ns.parser()
_list_parser.add_argument("tag", location="args", required=False, help="Filter by tag name")
_list_parser.add_argument("category", location="args", required=False, help="Filter by category")
_list_parser.add_argument(
    "file_type", location="args", required=False,
    help="Filter by file type",
    choices=("pdf", "latex", "dataset", "other"),
)
_list_parser.add_argument("page", location="args", type=int, default=1, help="Page number")
_list_parser.add_argument("per_page", location="args", type=int, default=20, help="Items per page (max 100)")


def _error(code, message, field=None, status=400):
    body = {"error": code, "message": message}
    if field:
        body["field"] = field
    return body, status


def _serialize_doc(doc):
    tags = [
        {"id": str(dt.tag.id), "name": dt.tag.name, "accepted": dt.accepted}
        for dt in doc.document_tags
    ]
    return {
        "id": str(doc.id),
        "title": doc.title,
        "description": doc.description,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "category": doc.category,
        "tags": tags,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }


@documents_ns.route("")
class DocumentList(Resource):
    @auth_required()
    @documents_ns.expect(_upload_parser)
    @documents_ns.doc(
        security="apikey",
        responses={201: "Created", 400: "Missing required field", 401: "Unauthorized", 422: "Invalid file_type"},
    )
    def post(self):
        """Upload a new document with metadata."""
        title = request.form.get("title", "").strip()
        if not title:
            return _error("missing_field", "Title is required.", field="title", status=400)

        file = request.files.get("file")
        if not file or not file.filename:
            return _error("missing_field", "File is required.", field="file", status=400)

        file_type = request.form.get("file_type", "").strip()
        if not file_type:
            return _error("missing_field", "file_type is required.", field="file_type", status=400)
        if file_type not in VALID_FILE_TYPES:
            return _error(
                "invalid_file_type",
                f"file_type must be one of: {', '.join(sorted(VALID_FILE_TYPES))}.",
                field="file_type",
                status=422,
            )

        description = request.form.get("description", "").strip() or None
        category = request.form.get("category", "").strip() or None

        doc_id = uuid.uuid4()
        storage_path = current_app.config.get("STORAGE_PATH", "/data")
        files_dir = os.path.join(storage_path, "files")
        os.makedirs(files_dir, exist_ok=True)
        file_path = os.path.join(files_dir, str(doc_id))

        file_bytes = file.read()
        file_size = len(file_bytes)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        doc = Document(
            id=doc_id,
            user_id=current_user.id,
            title=title,
            description=description,
            category=category,
            file_type=file_type,
            file_path=file_path,
            file_size=file_size,
        )
        db.session.add(doc)
        db.session.commit()

        return {"id": str(doc.id)}, 201

    @auth_required()
    @documents_ns.expect(_list_parser)
    @documents_ns.marshal_with(_document_list_model, code=200)
    @documents_ns.doc(
        security="apikey",
        responses={200: "OK", 401: "Unauthorized"},
    )
    def get(self):
        """List documents owned by the authenticated user with optional filtering."""
        tag_filter = request.args.get("tag", "").strip() or None
        category_filter = request.args.get("category", "").strip() or None
        file_type_filter = request.args.get("file_type", "").strip() or None

        try:
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 20))
        except (ValueError, TypeError):
            page, per_page = 1, 20

        page = max(1, page)
        per_page = min(max(1, per_page), 100)

        query = Document.query.filter_by(user_id=current_user.id)

        if tag_filter:
            query = (
                query
                .join(DocumentTag, Document.id == DocumentTag.document_id)
                .join(Tag, DocumentTag.tag_id == Tag.id)
                .filter(Tag.name == tag_filter)
            )

        if category_filter:
            query = query.filter(Document.category == category_filter)

        if file_type_filter:
            query = query.filter(Document.file_type == file_type_filter)

        pagination = query.order_by(Document.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            "items": [_serialize_doc(d) for d in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
        }, 200


@documents_ns.route("/<doc_id>")
class DocumentDetail(Resource):
    @auth_required()
    @documents_ns.marshal_with(_document_model, code=200)
    @documents_ns.doc(
        security="apikey",
        params={"doc_id": "Document UUID"},
        responses={200: "OK", 401: "Unauthorized", 404: "Not found"},
    )
    def get(self, doc_id):
        """Get full metadata for a single document owned by the authenticated user."""
        try:
            doc_uuid = uuid.UUID(doc_id)
        except (ValueError, AttributeError):
            return _error("not_found", "Document not found.", status=404)

        doc = Document.query.filter_by(id=doc_uuid, user_id=current_user.id).first()
        if doc is None:
            return _error("not_found", "Document not found.", status=404)

        return _serialize_doc(doc), 200

    @auth_required()
    @documents_ns.doc(
        security="apikey",
        params={"doc_id": "Document UUID"},
        responses={204: "Deleted", 401: "Unauthorized", 404: "Not found"},
    )
    def delete(self, doc_id):
        """Delete a document and all associated records and file blob."""
        try:
            doc_uuid = uuid.UUID(doc_id)
        except (ValueError, AttributeError):
            return _error("not_found", "Document not found.", status=404)

        doc = Document.query.filter_by(id=doc_uuid, user_id=current_user.id).first()
        if doc is None:
            return _error("not_found", "Document not found.", status=404)

        # Delete file blob from storage
        file_path = doc.file_path
        if file_path and os.path.isfile(file_path):
            os.remove(file_path)

        # Delete chunk files from storage
        storage_path = current_app.config.get("STORAGE_PATH", "/data")
        chunks_dir = os.path.join(storage_path, "chunks", str(doc_uuid))
        if os.path.isdir(chunks_dir):
            import shutil
            shutil.rmtree(chunks_dir)

        # Delete DB record (cascades to DocumentTag and UploadChunk via ORM)
        db.session.delete(doc)
        db.session.commit()

        return "", 204


@documents_ns.route("/<doc_id>/download")
class DocumentDownload(Resource):
    @auth_required()
    @documents_ns.doc(
        security="apikey",
        params={"doc_id": "Document UUID"},
        responses={
            200: "Binary file download",
            401: "Unauthorized",
            404: "Not found",
        },
        produces=["application/pdf", "application/x-latex", "application/octet-stream"],
    )
    def get(self, doc_id):
        """Download the file blob for a document owned by the authenticated user."""
        try:
            doc_uuid = uuid.UUID(doc_id)
        except (ValueError, AttributeError):
            return _error("not_found", "Document not found.", status=404)

        doc = Document.query.filter_by(id=doc_uuid, user_id=current_user.id).first()
        if doc is None:
            return _error("not_found", "Document not found.", status=404)

        file_path = doc.file_path
        if not file_path or not os.path.isfile(file_path):
            return _error("not_found", "File not found on storage.", status=404)

        mime_map = {
            "pdf": "application/pdf",
            "latex": "application/x-latex",
            "dataset": "application/octet-stream",
            "other": "application/octet-stream",
        }
        mimetype = mime_map.get(doc.file_type, "application/octet-stream")

        return send_file(file_path, mimetype=mimetype, as_attachment=True,
                         download_name=f"{doc_id}")


@documents_ns.route("/<doc_id>/status")
class DocumentStatus(Resource):
    @auth_required()
    @documents_ns.doc(
        security="apikey",
        params={"doc_id": "Document UUID"},
        responses={200: "OK", 401: "Unauthorized", 404: "Not found"},
    )
    def get(self, doc_id):
        """Get chunked upload status for a document — implemented in task 6.3."""
        pass
