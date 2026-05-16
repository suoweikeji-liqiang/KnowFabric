"""Add document triage and SHA-256 inventory fields.

Revision ID: 008
Revises: 437159d3c373
Create Date: 2026-05-14 19:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "008"
down_revision = "437159d3c373"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document", sa.Column("processing_decision", sa.String(32), nullable=True))
    op.add_column("document", sa.Column("processing_decision_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("document", sa.Column("processing_decision_reason", sa.Text(), nullable=True))
    op.add_column("document", sa.Column("file_sha256", sa.String(64), nullable=True))
    op.create_index("idx_document_file_sha256", "document", ["file_sha256"])
    op.execute("UPDATE document SET file_sha256 = file_hash WHERE file_sha256 IS NULL")


def downgrade() -> None:
    op.drop_index("idx_document_file_sha256", table_name="document")
    op.drop_column("document", "file_sha256")
    op.drop_column("document", "processing_decision_reason")
    op.drop_column("document", "processing_decision_at")
    op.drop_column("document", "processing_decision")
