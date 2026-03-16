from flask_sqlalchemy import SQLAlchemy
from flask_security import Security
from flask_restx import Api

db = SQLAlchemy()
security = Security()
api = Api(
    title="ResearchOS API",
    version="1.0",
    description=(
        "Self-hosted research document management platform. "
        "Authenticate via POST /auth/login, then click **Authorize** and enter: "
        "`your-token-here` (the value of the `token` field from the login response)."
    ),
    doc="/docs",
    authorizations={
        "apikey": {
            "type": "apiKey",
            "in": "header",
            "name": "Authentication-Token",
        }
    },
    security="apikey",
)
