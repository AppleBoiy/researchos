from flask import Blueprint

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """User registration — implemented in task 2."""
    pass


@auth_bp.route("/login", methods=["POST"])
def login():
    """User login — implemented in task 2."""
    pass
