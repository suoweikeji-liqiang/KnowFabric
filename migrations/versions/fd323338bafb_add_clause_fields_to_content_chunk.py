"""Add clause fields to content_chunk.

Revision ID: fd323338bafb
Revises: e8fa6e88442b
Create Date: 2026-05-11 10:26:43.047853

Additive migration — no data loss. Null for existing page-based chunks.
"""
from alembic import op
import sqlalchemy as sa


revision = 'fd323338bafb'
down_revision = 'e8fa6e88442b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('content_chunk', sa.Column('standard_clause', sa.String(64), nullable=True))
    op.add_column('content_chunk', sa.Column('clause_path', sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column('content_chunk', 'clause_path')
    op.drop_column('content_chunk', 'standard_clause')
