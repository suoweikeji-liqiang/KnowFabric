"""Add authority fields to knowledge_object and knowledge_object_evidence.

Revision ID: e8fa6e88442b
Revises: 06cf4a098b27
Create Date: 2026-05-11 10:26:16.594609

Additive migration — no data loss. Existing KO rows get consensus_state='single_source'.
"""
from alembic import op
import sqlalchemy as sa


revision = 'e8fa6e88442b'
down_revision = '06cf4a098b27'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('knowledge_object', sa.Column('authority_summary_json', sa.JSON, nullable=True))
    op.add_column('knowledge_object', sa.Column('consensus_state', sa.String(32), nullable=True))
    op.add_column('knowledge_object', sa.Column('conflict_summary', sa.Text, nullable=True))
    op.add_column('knowledge_object', sa.Column('highest_authority_level', sa.String(32), nullable=True))
    op.add_column('knowledge_object', sa.Column('deviation_justification_json', sa.JSON, nullable=True))

    op.execute("UPDATE knowledge_object SET consensus_state = 'single_source' WHERE consensus_state IS NULL")

    op.add_column('knowledge_object_evidence', sa.Column('authority_role', sa.String(64), nullable=True))
    op.add_column('knowledge_object_evidence', sa.Column('evidence_citation', sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_column('knowledge_object_evidence', 'evidence_citation')
    op.drop_column('knowledge_object_evidence', 'authority_role')
    op.drop_column('knowledge_object', 'deviation_justification_json')
    op.drop_column('knowledge_object', 'highest_authority_level')
    op.drop_column('knowledge_object', 'conflict_summary')
    op.drop_column('knowledge_object', 'consensus_state')
    op.drop_column('knowledge_object', 'authority_summary_json')
