import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
import sqlalchemy as sa

from app.extensions import db


# Cross-DB UUID type: uses native UUID on PostgreSQL, CHAR(36) on SQLite
class GUID(TypeDecorator):
    """Platform-independent GUID type."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(str(value)))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(str(value))
        return value


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Enums
FileTypeEnum = Enum("pdf", "latex", "dataset", "other", name="file_type_enum")
TransferTypeEnum = Enum("ssh", "s3", "local", name="transfer_type_enum")
TransferStatusEnum = Enum(
    "pending", "in_progress", "completed", "failed", name="transfer_status_enum"
)


class User(db.Model):
    __tablename__ = "user"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Flask-Security uses 'password'
    active = Column(Boolean(), default=True)
    fs_uniquifier = Column(String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    documents = db.relationship("Document", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Document(db.Model):
    __tablename__ = "document"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(1000), nullable=True)
    file_type = Column(FileTypeEnum, nullable=False)
    file_size = Column(BigInteger, nullable=True)
    category = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    user = db.relationship("User", back_populates="documents")
    document_tags = db.relationship(
        "DocumentTag", back_populates="document", cascade="all, delete-orphan"
    )
    upload_chunks = db.relationship(
        "UploadChunk", back_populates="document", cascade="all, delete-orphan"
    )
    transfer_jobs = db.relationship(
        "TransferJob", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Document {self.title}>"


class Tag(db.Model):
    __tablename__ = "tag"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)

    # Relationships
    document_tags = db.relationship("DocumentTag", back_populates="tag")

    def __repr__(self):
        return f"<Tag {self.name}>"


class DocumentTag(db.Model):
    __tablename__ = "document_tag"

    document_id = Column(
        GUID(), ForeignKey("document.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id = Column(
        GUID(), ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True
    )
    accepted = Column(Boolean, default=False, nullable=False)

    # Relationships
    document = db.relationship("Document", back_populates="document_tags")
    tag = db.relationship("Tag", back_populates="document_tags")

    def __repr__(self):
        return f"<DocumentTag doc={self.document_id} tag={self.tag_id}>"


class UploadChunk(db.Model):
    __tablename__ = "upload_chunk"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        GUID(), ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index = Column(Integer, nullable=False)
    total_chunks = Column(Integer, nullable=False)
    temp_path = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    document = db.relationship("Document", back_populates="upload_chunks")

    def __repr__(self):
        return f"<UploadChunk doc={self.document_id} idx={self.chunk_index}>"


class TransferJob(db.Model):
    __tablename__ = "transfer_job"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        GUID(), ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )

    # Source config
    source_type = Column(TransferTypeEnum, nullable=False)
    source_host = Column(String(255), nullable=True)
    source_port = Column(Integer, nullable=True)
    source_username = Column(String(255), nullable=True)
    source_key_path = Column(String(1000), nullable=True)
    source_path = Column(String(1000), nullable=True)

    # Destination config
    dest_type = Column(TransferTypeEnum, nullable=False)
    dest_host = Column(String(255), nullable=True)
    dest_port = Column(Integer, nullable=True)
    dest_username = Column(String(255), nullable=True)
    dest_key_path = Column(String(1000), nullable=True)
    dest_path = Column(String(1000), nullable=True)
    dest_bucket = Column(String(255), nullable=True)
    dest_prefix = Column(String(1000), nullable=True)

    # Status
    status = Column(TransferStatusEnum, nullable=False, default="pending")
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    document = db.relationship("Document", back_populates="transfer_jobs")

    def __repr__(self):
        return f"<TransferJob {self.id} status={self.status}>"
