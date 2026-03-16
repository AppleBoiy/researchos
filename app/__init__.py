import os

from flask import Flask

from app.config import config_map
from app.extensions import db, security, api


def create_app(config_name=None):
    """Flask application factory."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    cfg = config_map.get(config_name, config_map["development"])
    app.config.from_object(cfg)

    db.init_app(app)

    from app.security import setup_security
    setup_security(app)

    from app.auth.routes import auth_ns
    from app.documents.routes import documents_ns
    from app.chunks.routes import chunks_ns
    from app.transfers.routes import transfers_ns
    from app.tags.routes import tags_ns
    from app.llm.routes import llm_ns

    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(documents_ns, path="/documents")
    api.add_namespace(chunks_ns, path="/documents")
    api.add_namespace(transfers_ns, path="/transfers")
    api.add_namespace(tags_ns, path="/tags")
    api.add_namespace(llm_ns, path="/documents")

    api.init_app(app)

    return app
