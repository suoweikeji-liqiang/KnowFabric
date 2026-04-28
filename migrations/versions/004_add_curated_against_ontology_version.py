"""Add curated_against_ontology_version to knowledge objects.

Revision ID: 004
Revises: 003
Create Date: 2026-04-27
"""

from alembic import op
import sqlalchemy as sa


revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "knowledge_object",
        sa.Column("curated_against_ontology_version", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("knowledge_object", "curated_against_ontology_version")
