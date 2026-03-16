"""Unit tests for POST /documents endpoint."""
import io
import os
import uuid

import pytest


def _make_file(content=b"hello world", filename="test.pdf"):
    return (io.BytesIO(content), filename)


def _post_document(client, headers, title="My Doc", file_type="pdf",
                   file_content=b"data", filename="test.pdf",
                   description=None, category=None):
    data = {
        "title": title,
        "file_type": file_type,
        "file": _make_file(file_content, filename),
    }
    if description:
        data["description"] = description
    if category:
        data["category"] = category
    merged_headers = {"Accept": "application/json", **(headers or {})}
    return client.post(
        "/documents",
        data=data,
        content_type="multipart/form-data",
        headers=merged_headers,
    )


class TestPostDocuments:
    def test_create_document_returns_201_with_id(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _post_document(client, auth_headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert "id" in data
        # Should be a valid UUID
        uuid.UUID(data["id"])

    def test_create_document_stores_file(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        content = b"file content bytes"
        resp = _post_document(client, auth_headers, file_content=content)
        assert resp.status_code == 201
        doc_id = resp.get_json()["id"]
        stored = os.path.join(str(tmp_path), "files", doc_id)
        assert os.path.exists(stored)
        assert open(stored, "rb").read() == content

    def test_create_document_records_file_size(self, client, auth_headers, tmp_path, app):
        """Requirement 2.5: file_size must be recorded."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        content = b"exactly 18 bytes!!"
        resp = _post_document(client, auth_headers, file_content=content)
        assert resp.status_code == 201
        doc_id = resp.get_json()["id"]

        with app.app_context():
            from app.models import Document
            doc = Document.query.filter_by(id=uuid.UUID(doc_id)).first()
            assert doc is not None
            assert doc.file_size == len(content)

    def test_missing_title_returns_400(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        data = {
            "file_type": "pdf",
            "file": _make_file(),
        }
        resp = client.post(
            "/documents",
            data=data,
            content_type="multipart/form-data",
            headers={"Accept": "application/json", **auth_headers},
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["error"] == "missing_field"
        assert body["field"] == "title"

    def test_missing_file_returns_400(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        data = {"title": "My Doc", "file_type": "pdf"}
        resp = client.post(
            "/documents",
            data=data,
            content_type="multipart/form-data",
            headers={"Accept": "application/json", **auth_headers},
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["error"] == "missing_field"
        assert body["field"] == "file"

    def test_invalid_file_type_returns_422(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _post_document(client, auth_headers, file_type="docx")
        assert resp.status_code == 422
        body = resp.get_json()
        assert body["error"] == "invalid_file_type"
        assert body["field"] == "file_type"

    def test_valid_file_types_accepted(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        for ft in ("pdf", "latex", "dataset", "other"):
            resp = _post_document(client, auth_headers, file_type=ft, title=f"Doc {ft}")
            assert resp.status_code == 201, f"Expected 201 for file_type={ft}"

    def test_unauthenticated_returns_401(self, client, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        data = {
            "title": "My Doc",
            "file_type": "pdf",
            "file": _make_file(),
        }
        resp = client.post(
            "/documents",
            data=data,
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 401

    def test_optional_fields_stored(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _post_document(
            client, auth_headers,
            description="A description",
            category="physics",
        )
        assert resp.status_code == 201
        doc_id = resp.get_json()["id"]
        with app.app_context():
            from app.models import Document
            doc = Document.query.filter_by(id=uuid.UUID(doc_id)).first()
            assert doc.description == "A description"
            assert doc.category == "physics"


# ---------------------------------------------------------------------------
# GET /documents — listing and filtering (Task 3.4)
# ---------------------------------------------------------------------------

def _get_documents(client, headers, **params):
    merged_headers = {"Accept": "application/json", **(headers or {})}
    return client.get("/documents", query_string=params, headers=merged_headers)


class TestGetDocuments:
    def test_returns_200_with_empty_list(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _get_documents(client, auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_returns_owned_documents(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        _post_document(client, auth_headers, title="Doc A")
        _post_document(client, auth_headers, title="Doc B")
        resp = _get_documents(client, auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 2
        titles = {d["title"] for d in data["items"]}
        assert titles == {"Doc A", "Doc B"}

    def test_unauthenticated_returns_401(self, client, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _get_documents(client, {})
        assert resp.status_code == 401

    def test_filter_by_category(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        _post_document(client, auth_headers, title="Physics", category="physics")
        _post_document(client, auth_headers, title="Math", category="math")
        resp = _get_documents(client, auth_headers, category="physics")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Physics"

    def test_filter_by_file_type(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        _post_document(client, auth_headers, title="PDF Doc", file_type="pdf")
        _post_document(client, auth_headers, title="Dataset", file_type="dataset")
        resp = _get_documents(client, auth_headers, file_type="pdf")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "PDF Doc"

    def test_filter_by_tag(self, client, auth_headers, tmp_path, app, db):
        app.config["STORAGE_PATH"] = str(tmp_path)
        r1 = _post_document(client, auth_headers, title="Tagged Doc")
        _post_document(client, auth_headers, title="Untagged Doc")
        doc1_id = r1.get_json()["id"]

        # Insert tag association directly via DB
        with app.app_context():
            from app.models import Tag, DocumentTag
            tag = Tag(name="ml")
            db.session.add(tag)
            db.session.flush()
            dt = DocumentTag(document_id=uuid.UUID(doc1_id), tag_id=tag.id, accepted=True)
            db.session.add(dt)
            db.session.commit()

        resp = _get_documents(client, auth_headers, tag="ml")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Tagged Doc"

    def test_multiple_filters_applied_simultaneously(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        # Doc that matches both filters
        r1 = _post_document(client, auth_headers, title="Match", file_type="pdf", category="science")
        # Doc that matches only category
        _post_document(client, auth_headers, title="Only Category", file_type="dataset", category="science")
        # Doc that matches only file_type
        _post_document(client, auth_headers, title="Only Type", file_type="pdf", category="math")

        resp = _get_documents(client, auth_headers, file_type="pdf", category="science")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Match"

    def test_pagination_page_and_per_page(self, client, auth_headers, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        for i in range(5):
            _post_document(client, auth_headers, title=f"Doc {i}")
        resp = _get_documents(client, auth_headers, page=1, per_page=2)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["pages"] == 3

    def test_response_includes_tags_with_accepted_field(self, client, auth_headers, tmp_path, app, db):
        app.config["STORAGE_PATH"] = str(tmp_path)
        r = _post_document(client, auth_headers, title="Doc With Tag")
        doc_id = r.get_json()["id"]

        with app.app_context():
            from app.models import Tag, DocumentTag
            tag = Tag(name="ai")
            db.session.add(tag)
            db.session.flush()
            dt = DocumentTag(document_id=uuid.UUID(doc_id), tag_id=tag.id, accepted=True)
            db.session.add(dt)
            db.session.commit()

        resp = _get_documents(client, auth_headers)
        data = resp.get_json()
        doc = data["items"][0]
        assert "tags" in doc
        assert len(doc["tags"]) == 1
        assert doc["tags"][0]["name"] == "ai"
        assert "accepted" in doc["tags"][0]

    def test_isolation_between_users(self, client, auth_headers, tmp_path, app, db):
        """Query only returns documents owned by the authenticated user (user_id filter)."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        _post_document(client, auth_headers, title="User1 Doc")

        # Verify the query filters by user_id: create a document directly for a different user
        # and confirm it does NOT appear in user1's listing
        from app.models import Document
        other_user_id = uuid.uuid4()
        other_doc = Document(
            id=uuid.uuid4(),
            user_id=other_user_id,
            title="Other User Doc",
            file_type="pdf",
            file_size=0,
        )
        db.session.add(other_doc)
        db.session.commit()

        resp = _get_documents(client, auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "User1 Doc"


# ---------------------------------------------------------------------------
# GET /documents/<id> — single document fetch (Task 3.6)
# ---------------------------------------------------------------------------

def _get_document(client, headers, doc_id):
    merged_headers = {"Accept": "application/json", **(headers or {})}
    return client.get(f"/documents/{doc_id}", headers=merged_headers)


class TestGetDocumentById:
    def test_returns_full_metadata(self, client, auth_headers, tmp_path, app):
        """Req 3.6: GET /documents/<id> returns full metadata for owned document."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        create_resp = _post_document(
            client, auth_headers,
            title="My Paper",
            file_type="pdf",
            description="A description",
            category="science",
        )
        assert create_resp.status_code == 201
        doc_id = create_resp.get_json()["id"]

        resp = _get_document(client, auth_headers, doc_id)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["id"] == doc_id
        assert data["title"] == "My Paper"
        assert data["description"] == "A description"
        assert data["file_type"] == "pdf"
        assert data["category"] == "science"
        assert "file_size" in data
        assert "tags" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_returns_404_for_nonexistent_document(self, client, auth_headers, tmp_path, app):
        """Req 3.7: returns 404 when document does not exist."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _get_document(client, auth_headers, str(uuid.uuid4()))
        assert resp.status_code == 404

    def test_returns_404_for_other_users_document(self, client, auth_headers, tmp_path, app, db):
        """Req 3.7: returns 404 when document belongs to a different user."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        other_doc = None
        with app.app_context():
            from app.models import Document
            other_doc_id = uuid.uuid4()
            other_doc = Document(
                id=other_doc_id,
                user_id=uuid.uuid4(),
                title="Other User Doc",
                file_type="pdf",
                file_size=0,
            )
            db.session.add(other_doc)
            db.session.commit()

        resp = _get_document(client, auth_headers, str(other_doc_id))
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _get_document(client, {}, str(uuid.uuid4()))
        assert resp.status_code == 401

    def test_response_includes_tags(self, client, auth_headers, tmp_path, app, db):
        """Tags are included in the single-document response."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        r = _post_document(client, auth_headers, title="Tagged")
        doc_id = r.get_json()["id"]

        with app.app_context():
            from app.models import Tag, DocumentTag
            tag = Tag(name="nlp")
            db.session.add(tag)
            db.session.flush()
            dt = DocumentTag(document_id=uuid.UUID(doc_id), tag_id=tag.id, accepted=True)
            db.session.add(dt)
            db.session.commit()

        resp = _get_document(client, auth_headers, doc_id)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "nlp"
        assert data["tags"][0]["accepted"] is True


# ---------------------------------------------------------------------------
# GET /documents/<id>/download — file streaming (Task 4.1)
# ---------------------------------------------------------------------------

def _download_document(client, headers, doc_id):
    merged_headers = {"Accept": "application/json", **(headers or {})}
    return client.get(f"/documents/{doc_id}/download", headers=merged_headers)


class TestDownloadDocument:
    def test_streams_file_with_correct_content_type(self, client, auth_headers, tmp_path, app):
        """Req 4.1: streams file blob with correct Content-Type."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        content = b"%PDF-1.4 test content"
        resp = _post_document(client, auth_headers, file_content=content, file_type="pdf")
        assert resp.status_code == 201
        doc_id = resp.get_json()["id"]

        dl = _download_document(client, auth_headers, doc_id)
        assert dl.status_code == 200
        assert dl.data == content
        assert "application/pdf" in dl.content_type

    def test_streams_latex_with_correct_content_type(self, client, auth_headers, tmp_path, app):
        """Req 4.1: latex file_type returns application/x-latex."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        content = b"\\documentclass{article}"
        resp = _post_document(client, auth_headers, file_content=content, file_type="latex")
        assert resp.status_code == 201
        doc_id = resp.get_json()["id"]

        dl = _download_document(client, auth_headers, doc_id)
        assert dl.status_code == 200
        assert dl.data == content
        assert "application/x-latex" in dl.content_type

    def test_returns_404_when_file_missing_from_storage(self, client, auth_headers, tmp_path, app, db):
        """Req 4.2: 404 when file is not present on storage volume."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        # Create document record pointing to a non-existent file
        with app.app_context():
            from app.models import User, Document as Doc
            user = User.query.filter_by(email="testuser@example.com").first()
            doc_id = uuid.uuid4()
            doc = Doc(
                id=doc_id,
                user_id=user.id,
                title="Missing File",
                file_type="pdf",
                file_size=0,
                file_path="/nonexistent/path/to/file",
            )
            db.session.add(doc)
            db.session.commit()

        dl = _download_document(client, auth_headers, str(doc_id))
        assert dl.status_code == 404

    def test_returns_404_for_other_users_document(self, client, auth_headers, tmp_path, app, db):
        """Req 4.3: 404 when document belongs to a different user."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        with app.app_context():
            from app.models import Document as Doc
            other_doc_id = uuid.uuid4()
            other_doc = Doc(
                id=other_doc_id,
                user_id=uuid.uuid4(),
                title="Other User Doc",
                file_type="pdf",
                file_size=5,
                file_path=str(tmp_path / "files" / str(other_doc_id)),
            )
            db.session.add(other_doc)
            db.session.commit()

        dl = _download_document(client, auth_headers, str(other_doc_id))
        assert dl.status_code == 404

    def test_returns_404_for_nonexistent_document(self, client, auth_headers, tmp_path, app):
        """404 for a completely unknown document ID."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        dl = _download_document(client, auth_headers, str(uuid.uuid4()))
        assert dl.status_code == 404

    def test_unauthenticated_returns_401(self, client, tmp_path, app):
        """Unauthenticated request returns 401."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        dl = _download_document(client, {}, str(uuid.uuid4()))
        assert dl.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /documents/<id> — document deletion (Task 4.4)
# ---------------------------------------------------------------------------

def _delete_document(client, headers, doc_id):
    merged_headers = {"Accept": "application/json", **(headers or {})}
    return client.delete(f"/documents/{doc_id}", headers=merged_headers)


class TestDeleteDocument:
    def test_delete_returns_204(self, client, auth_headers, tmp_path, app):
        """Req 5.3: successful delete returns 204 No Content."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _post_document(client, auth_headers)
        doc_id = resp.get_json()["id"]

        del_resp = _delete_document(client, auth_headers, doc_id)
        assert del_resp.status_code == 204

    def test_delete_removes_document_record(self, client, auth_headers, tmp_path, app):
        """Req 5.1: Document record is removed from DB."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _post_document(client, auth_headers)
        doc_id = resp.get_json()["id"]

        _delete_document(client, auth_headers, doc_id)

        with app.app_context():
            from app.models import Document
            assert Document.query.filter_by(id=uuid.UUID(doc_id)).first() is None

    def test_delete_removes_file_blob(self, client, auth_headers, tmp_path, app):
        """Req 5.1: file blob is removed from storage."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _post_document(client, auth_headers, file_content=b"blob data")
        doc_id = resp.get_json()["id"]
        file_path = tmp_path / "files" / doc_id
        assert file_path.exists()

        _delete_document(client, auth_headers, doc_id)
        assert not file_path.exists()

    def test_delete_removes_document_tags(self, client, auth_headers, tmp_path, app, db):
        """Req 5.1: associated DocumentTag records are removed."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _post_document(client, auth_headers)
        doc_id = resp.get_json()["id"]

        with app.app_context():
            from app.models import Tag, DocumentTag
            tag = Tag(name="to-delete")
            db.session.add(tag)
            db.session.flush()
            dt = DocumentTag(document_id=uuid.UUID(doc_id), tag_id=tag.id, accepted=False)
            db.session.add(dt)
            db.session.commit()

        _delete_document(client, auth_headers, doc_id)

        with app.app_context():
            from app.models import DocumentTag
            assert DocumentTag.query.filter_by(document_id=uuid.UUID(doc_id)).count() == 0

    def test_delete_removes_upload_chunks(self, client, auth_headers, tmp_path, app, db):
        """Req 5.1: associated UploadChunk records are removed."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _post_document(client, auth_headers)
        doc_id = resp.get_json()["id"]

        with app.app_context():
            from app.models import UploadChunk
            chunk = UploadChunk(
                document_id=uuid.UUID(doc_id),
                chunk_index=0,
                total_chunks=1,
                temp_path="/tmp/chunk0",
            )
            db.session.add(chunk)
            db.session.commit()

        _delete_document(client, auth_headers, doc_id)

        with app.app_context():
            from app.models import UploadChunk
            assert UploadChunk.query.filter_by(document_id=uuid.UUID(doc_id)).count() == 0

    def test_delete_returns_404_for_other_users_document(self, client, auth_headers, tmp_path, app, db):
        """Req 5.2: 404 when document belongs to a different user."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        with app.app_context():
            from app.models import Document
            other_doc_id = uuid.uuid4()
            other_doc = Document(
                id=other_doc_id,
                user_id=uuid.uuid4(),
                title="Other User Doc",
                file_type="pdf",
                file_size=0,
            )
            db.session.add(other_doc)
            db.session.commit()

        resp = _delete_document(client, auth_headers, str(other_doc_id))
        assert resp.status_code == 404

    def test_delete_returns_404_for_nonexistent_document(self, client, auth_headers, tmp_path, app):
        """Req 5.2: 404 for unknown document ID."""
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _delete_document(client, auth_headers, str(uuid.uuid4()))
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client, tmp_path, app):
        app.config["STORAGE_PATH"] = str(tmp_path)
        resp = _delete_document(client, {}, str(uuid.uuid4()))
        assert resp.status_code == 401
