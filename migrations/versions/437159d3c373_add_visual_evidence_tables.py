"""Add visual evidence tables (document_page_image + visual_evidence_anchor).

Revision ID: 437159d3c373
Revises: fd323338bafb
Create Date: 2026-05-11 11:48:16.428618

Additive migration — two new tables, no data migration needed.
"""
from alembic import op
import sqlalchemy as sa


revision = '437159d3c373'
down_revision = 'fd323338bafb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'document_page_image',
        sa.Column('page_image_id', sa.String(64), primary_key=True),
        sa.Column('doc_id', sa.String(64), sa.ForeignKey('document.doc_id'), nullable=False),
        sa.Column('page_id', sa.String(64), sa.ForeignKey('document_page.page_id'), nullable=False),
        sa.Column('page_no', sa.Integer, nullable=False),
        sa.Column('image_path', sa.String(512), nullable=False),
        sa.Column('bbox', sa.JSON, nullable=True),
        sa.Column('image_type', sa.String(32), nullable=False, server_default='other'),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('ocr_text', sa.Text, nullable=True),
        sa.Column('vl_summary', sa.Text, nullable=True),
        sa.Column('vl_entities_json', sa.JSON, nullable=True),
        sa.Column('vl_relationships_json', sa.JSON, nullable=True),
        sa.Column('useful_for_knowledge_types', sa.JSON, nullable=True),
        sa.Column('uncertainty_notes', sa.Text, nullable=True),
        sa.Column('vl_model', sa.String(64), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_page_image_doc_page', 'document_page_image', ['doc_id', 'page_no'])
    op.create_index('idx_page_image_type', 'document_page_image', ['image_type'])

    op.create_table(
        'visual_evidence_anchor',
        sa.Column('visual_evidence_id', sa.String(64), primary_key=True),
        sa.Column('knowledge_object_id', sa.String(64), sa.ForeignKey('knowledge_object.knowledge_object_id'), nullable=False),
        sa.Column('page_image_id', sa.String(64), sa.ForeignKey('document_page_image.page_image_id'), nullable=False),
        sa.Column('doc_id', sa.String(64), sa.ForeignKey('document.doc_id'), nullable=False),
        sa.Column('page_id', sa.String(64), sa.ForeignKey('document_page.page_id'), nullable=False),
        sa.Column('page_no', sa.Integer, nullable=False),
        sa.Column('bbox', sa.JSON, nullable=True),
        sa.Column('evidence_role', sa.String(32), nullable=False, server_default='primary_visual'),
        sa.Column('extracted_entities_json', sa.JSON, nullable=True),
        sa.Column('extracted_relationships_json', sa.JSON, nullable=True),
        sa.Column('model_used', sa.String(64), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint('uq_visual_evidence_anchor_ref', 'visual_evidence_anchor', ['knowledge_object_id', 'page_image_id', 'evidence_role'])
    op.create_index('idx_visual_evidence_trace', 'visual_evidence_anchor', ['knowledge_object_id', 'doc_id', 'page_no'])


def downgrade() -> None:
    op.drop_table('visual_evidence_anchor')
    op.drop_table('document_page_image')
