"""Create baseline tables

Revision ID: 001
Revises:
Create Date: 2026-03-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create document table
    op.create_table(
        'document',
        sa.Column('doc_id', sa.String(64), primary_key=True),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('storage_path', sa.String(1024), nullable=False),
        sa.Column('file_name', sa.String(512), nullable=False),
        sa.Column('file_ext', sa.String(32)),
        sa.Column('mime_type', sa.String(128)),
        sa.Column('file_size', sa.Integer()),
        sa.Column('source_domain', sa.String(64)),
        sa.Column('source_batch_id', sa.String(64)),
        sa.Column('parse_status', sa.String(32), server_default='pending'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('import_time', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_document_hash', 'document', ['file_hash'])
    op.create_index('idx_document_domain', 'document', ['source_domain'])

    # Create document_page table
    op.create_table(
        'document_page',
        sa.Column('page_id', sa.String(64), primary_key=True),
        sa.Column('doc_id', sa.String(64), sa.ForeignKey('document.doc_id'), nullable=False),
        sa.Column('page_no', sa.Integer(), nullable=False),
        sa.Column('raw_text', sa.Text()),
        sa.Column('cleaned_text', sa.Text(), nullable=False),
        sa.Column('page_image_path', sa.String(1024)),
        sa.Column('page_type', sa.String(32)),
        sa.Column('has_table', sa.Boolean(), server_default='false'),
        sa.Column('has_diagram', sa.Boolean(), server_default='false'),
        sa.Column('ocr_status', sa.String(32)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_page_doc_id', 'document_page', ['doc_id'])
    op.create_index('idx_page_doc_page_no', 'document_page', ['doc_id', 'page_no'])

    # Create content_chunk table
    op.create_table(
        'content_chunk',
        sa.Column('chunk_id', sa.String(64), primary_key=True),
        sa.Column('doc_id', sa.String(64), sa.ForeignKey('document.doc_id'), nullable=False),
        sa.Column('page_id', sa.String(64), sa.ForeignKey('document_page.page_id'), nullable=False),
        sa.Column('page_no', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('raw_text', sa.Text()),
        sa.Column('cleaned_text', sa.Text(), nullable=False),
        sa.Column('text_excerpt', sa.String(512)),
        sa.Column('chunk_type', sa.String(32), nullable=False),
        sa.Column('evidence_anchor', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_chunk_doc_id', 'content_chunk', ['doc_id'])
    op.create_index('idx_chunk_page_id', 'content_chunk', ['page_id'])
    op.create_index('idx_chunk_page_no', 'content_chunk', ['page_no'])
    op.create_index('idx_chunk_doc_page', 'content_chunk', ['doc_id', 'page_no'])

    # Create processing_job table
    op.create_table(
        'processing_job',
        sa.Column('job_id', sa.String(64), primary_key=True),
        sa.Column('job_type', sa.String(64), nullable=False),
        sa.Column('target_doc_id', sa.String(64), sa.ForeignKey('document.doc_id')),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_job_type', 'processing_job', ['job_type'])
    op.create_index('idx_job_doc_id', 'processing_job', ['target_doc_id'])
    op.create_index('idx_job_status', 'processing_job', ['status'])

    # Create processing_stage_log table
    op.create_table(
        'processing_stage_log',
        sa.Column('stage_id', sa.String(64), primary_key=True),
        sa.Column('job_id', sa.String(64), sa.ForeignKey('processing_job.job_id'), nullable=False),
        sa.Column('stage_name', sa.String(64), nullable=False),
        sa.Column('doc_id', sa.String(64), sa.ForeignKey('document.doc_id')),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('elapsed_ms', sa.Integer()),
        sa.Column('error_message', sa.Text()),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_stage_job_id', 'processing_stage_log', ['job_id'])
    op.create_index('idx_stage_doc_id', 'processing_stage_log', ['doc_id'])
    op.create_index('idx_stage_job_doc', 'processing_stage_log', ['job_id', 'doc_id'])


def downgrade() -> None:
    op.drop_table('processing_stage_log')
    op.drop_table('processing_job')
    op.drop_table('content_chunk')
    op.drop_table('document_page')
    op.drop_table('document')
