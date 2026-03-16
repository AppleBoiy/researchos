from flask import Blueprint

documents_bp = Blueprint("documents", __name__)


@documents_bp.route("", methods=["POST"])
def create_document():
    """Create document — implemented in task 3."""
    pass


@documents_bp.route("", methods=["GET"])
def list_documents():
    """List documents — implemented in task 3."""
    pass


@documents_bp.route("/<doc_id>", methods=["GET"])
def get_document(doc_id):
    """Get document — implemented in task 3."""
    pass


@documents_bp.route("/<doc_id>/download", methods=["GET"])
def download_document(doc_id):
    """Download document — implemented in task 4."""
    pass


@documents_bp.route("/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """Delete document — implemented in task 4."""
    pass


@documents_bp.route("/<doc_id>/status", methods=["GET"])
def document_status(doc_id):
    """Document upload status — implemented in task 6."""
    pass
