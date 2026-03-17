"""Create semantic knowledge tables for rebuild track

Revision ID: 003
Revises: 002
Create Date: 2026-03-17

"""
from alembic import op
import sqlalchemy as sa


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chunk_ontology_anchor",
        sa.Column("chunk_anchor_id", sa.String(64), primary_key=True),
        sa.Column("chunk_id", sa.String(64), sa.ForeignKey("content_chunk.chunk_id"), nullable=False),
        sa.Column("ontology_class_key", sa.String(196), sa.ForeignKey("ontology_class.ontology_class_key"), nullable=False),
        sa.Column("domain_id", sa.String(64), nullable=False),
        sa.Column("ontology_class_id", sa.String(128), nullable=False),
        sa.Column("match_method", sa.String(32), nullable=False, server_default="rule"),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("match_metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("chunk_id", "ontology_class_key", name="uq_chunk_ontology_anchor"),
    )
    op.create_index("idx_chunk_ontology_anchor_chunk_id", "chunk_ontology_anchor", ["chunk_id"])
    op.create_index(
        "idx_chunk_ontology_anchor_class_chunk",
        "chunk_ontology_anchor",
        ["ontology_class_key", "chunk_id"],
    )
    op.create_index("idx_chunk_ontology_anchor_domain_id", "chunk_ontology_anchor", ["domain_id"])

    op.create_table(
        "knowledge_object",
        sa.Column("knowledge_object_id", sa.String(64), primary_key=True),
        sa.Column("domain_id", sa.String(64), nullable=False),
        sa.Column("ontology_class_key", sa.String(196), sa.ForeignKey("ontology_class.ontology_class_key"), nullable=False),
        sa.Column("ontology_class_id", sa.String(128), nullable=False),
        sa.Column("knowledge_object_type", sa.String(64), nullable=False),
        sa.Column("canonical_key", sa.String(255), nullable=False),
        sa.Column("title", sa.String(512)),
        sa.Column("summary", sa.Text()),
        sa.Column("structured_payload_json", sa.JSON(), nullable=False),
        sa.Column("applicability_json", sa.JSON()),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("trust_level", sa.String(16), nullable=False, server_default="L4"),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("primary_chunk_id", sa.String(64), sa.ForeignKey("content_chunk.chunk_id"), nullable=False),
        sa.Column("package_version", sa.String(32), nullable=False),
        sa.Column("ontology_version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "domain_id",
            "ontology_class_id",
            "knowledge_object_type",
            "canonical_key",
            name="uq_knowledge_object_canonical_key",
        ),
    )
    op.create_index("idx_knowledge_object_domain_id", "knowledge_object", ["domain_id"])
    op.create_index(
        "idx_knowledge_object_anchor_type",
        "knowledge_object",
        ["ontology_class_key", "knowledge_object_type"],
    )
    op.create_index("idx_knowledge_object_primary_chunk_id", "knowledge_object", ["primary_chunk_id"])

    op.create_table(
        "knowledge_object_evidence",
        sa.Column("knowledge_evidence_id", sa.String(64), primary_key=True),
        sa.Column("knowledge_object_id", sa.String(64), sa.ForeignKey("knowledge_object.knowledge_object_id"), nullable=False),
        sa.Column("chunk_id", sa.String(64), sa.ForeignKey("content_chunk.chunk_id"), nullable=False),
        sa.Column("doc_id", sa.String(64), sa.ForeignKey("document.doc_id"), nullable=False),
        sa.Column("page_id", sa.String(64), sa.ForeignKey("document_page.page_id"), nullable=False),
        sa.Column("page_no", sa.Integer(), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("evidence_role", sa.String(32), nullable=False, server_default="supporting"),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "knowledge_object_id",
            "chunk_id",
            "evidence_role",
            name="uq_knowledge_object_evidence_ref",
        ),
    )
    op.create_index("idx_knowledge_object_evidence_chunk_id", "knowledge_object_evidence", ["chunk_id"])
    op.create_index(
        "idx_knowledge_object_evidence_trace",
        "knowledge_object_evidence",
        ["knowledge_object_id", "doc_id", "page_no"],
    )


def downgrade() -> None:
    op.drop_table("knowledge_object_evidence")
    op.drop_table("knowledge_object")
    op.drop_table("chunk_ontology_anchor")
