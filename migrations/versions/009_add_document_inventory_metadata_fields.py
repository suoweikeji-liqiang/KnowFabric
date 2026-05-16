"""Add document inventory metadata fields.

Revision ID: 009
Revises: 008
Create Date: 2026-05-14 19:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document", sa.Column("text_quality", sa.String(32), nullable=True))
    op.add_column("document", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column("document", sa.Column("sample_text_chars_first_3_pages", sa.Integer(), nullable=True))
    op.add_column("document", sa.Column("inventory_source_path", sa.String(1024), nullable=True))
    op.create_index("idx_document_text_quality", "document", ["text_quality"])
    op.create_index("idx_document_page_count", "document", ["page_count"])


def downgrade() -> None:
    op.drop_index("idx_document_page_count", table_name="document")
    op.drop_index("idx_document_text_quality", table_name="document")
    op.drop_column("document", "inventory_source_path")
    op.drop_column("document", "sample_text_chars_first_3_pages")
    op.drop_column("document", "page_count")
    op.drop_column("document", "text_quality")
