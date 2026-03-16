from flask import Blueprint

transfers_bp = Blueprint("transfers", __name__)


@transfers_bp.route("", methods=["POST"])
def create_transfer():
    """Create transfer job — implemented in task 7."""
    pass


@transfers_bp.route("/<job_id>", methods=["GET"])
def get_transfer(job_id):
    """Get transfer job — implemented in task 7."""
    pass
