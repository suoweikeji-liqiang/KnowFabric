"""Add authority fields to document table.

Revision ID: 06cf4a098b27
Revises: 007
Create Date: 2026-05-11 10:18:46.500963

Additive migration — no data loss. Existing rows get safe defaults:
authority_level='unspecified', is_redistributable=false, language='en',
authority_review_status='auto_suggested'.
"""
from alembic import op
import sqlalchemy as sa


revision = '06cf4a098b27'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('document', sa.Column('authority_level', sa.String(32), nullable=True))
    op.add_column('document', sa.Column('publisher', sa.String(128), nullable=True))
    op.add_column('document', sa.Column('standard_id', sa.String(128), nullable=True))
    op.add_column('document', sa.Column('publication_year', sa.Integer, nullable=True))
    op.add_column('document', sa.Column('revision', sa.String(64), nullable=True))
    op.add_column('document', sa.Column('regulatory_scope', sa.String(32), nullable=True))
    op.add_column('document', sa.Column('vendor_brand', sa.String(128), nullable=True))
    op.add_column('document', sa.Column('vendor_model_family', sa.String(128), nullable=True))
    op.add_column('document', sa.Column('applies_to_equipment_classes_json', sa.JSON, nullable=True))
    op.add_column('document', sa.Column('language', sa.String(16), nullable=True))
    op.add_column('document', sa.Column('authority_metadata_json', sa.JSON, nullable=True))
    op.add_column('document', sa.Column('is_redistributable', sa.Boolean, nullable=False, server_default=sa.text('false')))
    op.add_column('document', sa.Column('authority_review_status', sa.String(32), nullable=True))

    op.execute("UPDATE document SET authority_level = 'unspecified' WHERE authority_level IS NULL")
    op.execute("UPDATE document SET language = 'en' WHERE language IS NULL")
    op.execute("UPDATE document SET authority_review_status = 'auto_suggested' WHERE authority_review_status IS NULL")


def downgrade() -> None:
    op.drop_column('document', 'authority_review_status')
    op.drop_column('document', 'is_redistributable')
    op.drop_column('document', 'authority_metadata_json')
    op.drop_column('document', 'language')
    op.drop_column('document', 'applies_to_equipment_classes_json')
    op.drop_column('document', 'vendor_model_family')
    op.drop_column('document', 'vendor_brand')
    op.drop_column('document', 'regulatory_scope')
    op.drop_column('document', 'revision')
    op.drop_column('document', 'publication_year')
    op.drop_column('document', 'standard_id')
    op.drop_column('document', 'publisher')
    op.drop_column('document', 'authority_level')
