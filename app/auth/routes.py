import bcrypt
from flask import request
from flask_restx import Namespace, Resource, fields

from app.extensions import db
from app.models import User

auth_ns = Namespace("auth", description="Authentication")

_register_model = auth_ns.model("RegisterRequest", {
    "email": fields.String(required=True, example="user@example.com"),
    "password": fields.String(required=True, example="secret"),
})

_login_model = auth_ns.model("LoginRequest", {
    "email": fields.String(required=True, example="user@example.com"),
    "password": fields.String(required=True, example="secret"),
})


def _error(code, message, field=None, status=400):
    body = {"error": code, "message": message}
    if field:
        body["field"] = field
    return body, status


@auth_ns.route("/register")
class Register(Resource):
    @auth_ns.expect(_register_model)
    @auth_ns.doc(responses={201: "Created", 400: "Bad Request", 409: "Conflict"})
    def post(self):
        """Create a new user account."""
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email:
            return _error("missing_field", "Email is required.", field="email", status=400)
        if not password:
            return _error("missing_field", "Password is required.", field="password", status=400)

        if User.query.filter_by(email=email).first():
            return _error("email_taken", "An account with that email already exists.", field="email", status=409)

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(email=email, password=password_hash)
        db.session.add(user)
        db.session.commit()

        return {"id": str(user.id), "email": user.email}, 201


@auth_ns.route("/login")
class Login(Resource):
    @auth_ns.expect(_login_model)
    @auth_ns.doc(responses={200: "OK", 400: "Bad Request", 401: "Unauthorized"})
    def post(self):
        """Validate credentials and return a signed JWT."""
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return _error("missing_field", "Email and password are required.", status=400)

        user = User.query.filter_by(email=email).first()
        if not user or not user.active:
            return _error("invalid_credentials", "Invalid email or password.", status=401)

        if not bcrypt.checkpw(password.encode(), user.password.encode()):
            return _error("invalid_credentials", "Invalid email or password.", status=401)

        token = user.get_auth_token()
        return {"token": token}, 200
