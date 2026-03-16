from flask import Blueprint

llm_bp = Blueprint("llm", __name__)


@llm_bp.route("/<doc_id>/autotag", methods=["POST"])
def autotag(doc_id):
    """LLM auto-tagging — implemented in task 10."""
    pass
