from flask import Blueprint

tags_bp = Blueprint("tags", __name__)


@tags_bp.route("/tags", methods=["GET"])
def list_tags():
    """List all tags — implemented in task 9."""
    pass


@tags_bp.route("/documents/<doc_id>/tags", methods=["POST"])
def add_tags(doc_id):
    """Add tags to document — implemented in task 9."""
    pass


@tags_bp.route("/documents/<doc_id>/tags/<tag_id>", methods=["PATCH"])
def update_tag(doc_id, tag_id):
    """Accept/reject tag — implemented in task 9."""
    pass
