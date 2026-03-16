"""
Shared test fixtures for ResearchOS test suite.
"""
import os
import uuid
from unittest.mock import MagicMock, patch

import pytest

# Use testing config
os.environ.setdefault("FLASK_ENV", "testing")


@pytest.fixture(scope="session")
def app():
    """Create Flask application configured for testing with SQLite in-memory DB."""
    from app import create_app

    flask_app = create_app("testing")
    flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECURITY_CSRF_PROTECT_MECHANISMS": [],
        }
    )
    yield flask_app


@pytest.fixture(scope="function")
def db(app):
    """Provide a clean database for each test."""
    from app.extensions import db as _db

    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    """Flask test client with a fresh database."""
    with app.test_client() as c:
        yield c


@pytest.fixture(scope="function")
def auth_headers(client, db, app):
    """
    Register a test user and return JWT Authorization headers.
    Returns a dict with 'Authorization' header ready for use.
    """
    with app.app_context():
        from app.extensions import db as _db
        from app.models import User
        from app.security import Role
        import bcrypt

        # Create test user directly in DB
        password_hash = bcrypt.hashpw(b"testpassword123", bcrypt.gensalt()).decode()
        user = User(
            id=uuid.uuid4(),
            email="testuser@example.com",
            password=password_hash,
            active=True,
            fs_uniquifier=str(uuid.uuid4()),
        )
        _db.session.add(user)
        _db.session.commit()

        # Login to get JWT token
        response = client.post(
            "/auth/login",
            json={"email": "testuser@example.com", "password": "testpassword123"},
        )

        if response.status_code == 200:
            data = response.get_json()
            token = data.get("token") or data.get("access_token") or data.get("auth_token")
            if token:
                # Flask-Security token auth uses Authentication-Token header
                return {"Authentication-Token": token}

        # Fallback: return empty headers (auth not yet implemented)
        return {}


@pytest.fixture
def test_user(db, app):
    """Create and return a test user in the database."""
    with app.app_context():
        from app.models import User
        import bcrypt

        password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
        user = User(
            id=uuid.uuid4(),
            email=f"user_{uuid.uuid4().hex[:8]}@example.com",
            password=password_hash,
            active=True,
            fs_uniquifier=str(uuid.uuid4()),
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


# ---------------------------------------------------------------------------
# Mock factories
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ssh():
    """Mock factory for Paramiko SSH connections."""
    with patch("paramiko.SSHClient") as mock_ssh_class:
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client

        # Mock SFTP
        mock_sftp = MagicMock()
        mock_client.open_sftp.return_value = mock_sftp

        # Mock SCP-style file transfer
        mock_sftp.get = MagicMock()
        mock_sftp.put = MagicMock()

        yield {
            "ssh_class": mock_ssh_class,
            "client": mock_client,
            "sftp": mock_sftp,
        }


@pytest.fixture
def mock_s3():
    """Mock factory for S3 using moto."""
    try:
        import boto3
        from moto import mock_aws

        with mock_aws():
            s3 = boto3.client(
                "s3",
                region_name="us-east-1",
                aws_access_key_id="test",
                aws_secret_access_key="test",
            )
            s3.create_bucket(Bucket="test-bucket")
            yield {"client": s3, "bucket": "test-bucket"}
    except ImportError:
        # moto not installed — yield a plain mock
        mock_client = MagicMock()
        yield {"client": mock_client, "bucket": "test-bucket"}


@pytest.fixture
def mock_llm():
    """Mock factory for LLM API calls (OpenAI / Gemini)."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="machine learning, neural networks, deep learning, NLP, transformers"))
    ]

    with patch("openai.OpenAI") as mock_openai_class:
        mock_openai = MagicMock()
        mock_openai_class.return_value = mock_openai
        mock_openai.chat.completions.create.return_value = mock_response

        yield {
            "openai_class": mock_openai_class,
            "client": mock_openai,
            "response": mock_response,
            "tags": ["machine learning", "neural networks", "deep learning", "NLP", "transformers"],
        }
