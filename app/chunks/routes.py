from flask import Blueprint

chunks_bp = Blueprint("chunks", __name__)


@chunks_bp.route("/<doc_id>/chunks", methods=["POST"])
def upload_chunk(doc_id):
    """Upload chunk — implemented in task 6."""
    pass
