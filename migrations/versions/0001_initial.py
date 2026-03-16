"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # role table
    op.create_table(
        "role",
        sa.Column("id", sa.CHAR(36), nullable=False),
        sa.Column("name", sa.String(80), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # user table
    op.create_table(
        "user",
        sa.Column("id", sa.CHAR(36), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("fs_uniquifier", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("fs_uniquifier"),
    )

    # roles_users association table
    op.create_table(
        "roles_users",
        sa.Column("user_id", sa.CHAR(36), nullable=True),
        sa.Column("role_id", sa.CHAR(36), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )

    # document table
    op.create_table(
        "document",
        sa.Column("id", sa.CHAR(36), nullable=False),
        sa.Column("user_id", sa.CHAR(36), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column(
            "file_type",
            sa.Enum("pdf", "latex", "dataset", "other", name="file_type_enum"),
            nullable=False,
        ),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # tag table
    op.create_table(
        "tag",
        sa.Column("id", sa.CHAR(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # document_tag table
    op.create_table(
        "document_tag",
        sa.Column("document_id", sa.CHAR(36), nullable=False),
        sa.Column("tag_id", sa.CHAR(36), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("document_id", "tag_id"),
    )

    # upload_chunk table
    op.create_table(
        "upload_chunk",
        sa.Column("id", sa.CHAR(36), nullable=False),
        sa.Column("document_id", sa.CHAR(36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("total_chunks", sa.Integer(), nullable=False),
        sa.Column("temp_path", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # transfer_job table
    op.create_table(
        "transfer_job",
        sa.Column("id", sa.CHAR(36), nullable=False),
        sa.Column("document_id", sa.CHAR(36), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum("ssh", "s3", "local", name="transfer_type_enum"),
            nullable=False,
        ),
        sa.Column("source_host", sa.String(255), nullable=True),
        sa.Column("source_port", sa.Integer(), nullable=True),
        sa.Column("source_username", sa.String(255), nullable=True),
        sa.Column("source_key_path", sa.String(1000), nullable=True),
        sa.Column("source_path", sa.String(1000), nullable=True),
        sa.Column(
            "dest_type",
            sa.Enum("ssh", "s3", "local", name="transfer_type_enum"),
            nullable=False,
        ),
        sa.Column("dest_host", sa.String(255), nullable=True),
        sa.Column("dest_port", sa.Integer(), nullable=True),
        sa.Column("dest_username", sa.String(255), nullable=True),
        sa.Column("dest_key_path", sa.String(1000), nullable=True),
        sa.Column("dest_path", sa.String(1000), nullable=True),
        sa.Column("dest_bucket", sa.String(255), nullable=True),
        sa.Column("dest_prefix", sa.String(1000), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "in_progress", "completed", "failed",
                name="transfer_status_enum",
            ),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("transfer_job")
    op.drop_table("upload_chunk")
    op.drop_table("document_tag")
    op.drop_table("tag")
    op.drop_table("document")
    op.drop_table("roles_users")
    op.drop_table("user")
    op.drop_table("role")
    # Drop enums (PostgreSQL only)
    op.execute("DROP TYPE IF EXISTS file_type_enum")
    op.execute("DROP TYPE IF EXISTS transfer_type_enum")
    op.execute("DROP TYPE IF EXISTS transfer_status_enum")
