import os

from flask import Flask, jsonify
from flask_security import SQLAlchemyUserDatastore

from app.config import config_map
from app.extensions import db, security


def create_app(config_name=None):
    """Flask application factory."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    cfg = config_map.get(config_name, config_map["development"])
    app.config.from_object(cfg)

    # Initialize extensions
    db.init_app(app)

    # Set up Flask-Security
    from app.models import User
    from flask_security import SQLAlchemyUserDatastore

    # Flask-Security requires a Role model; we use a minimal stub
    from app.security import setup_security
    setup_security(app)

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.documents.routes import documents_bp
    from app.chunks.routes import chunks_bp
    from app.transfers.routes import transfers_bp
    from app.tags.routes import tags_bp
    from app.llm.routes import llm_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(documents_bp, url_prefix="/documents")
    app.register_blueprint(chunks_bp, url_prefix="/documents")
    app.register_blueprint(transfers_bp, url_prefix="/transfers")
    app.register_blueprint(tags_bp, url_prefix="")
    app.register_blueprint(llm_bp, url_prefix="/documents")

    @app.get("/")
    def health():
        return jsonify({"status": "ok", "service": "researchos"})

    return app
