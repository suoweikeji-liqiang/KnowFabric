"""Create ontology metadata tables for rebuild track

Revision ID: 002
Revises: 001
Create Date: 2026-03-17

"""
from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ontology_class",
        sa.Column("ontology_class_key", sa.String(196), primary_key=True),
        sa.Column("domain_id", sa.String(64), nullable=False),
        sa.Column("ontology_class_id", sa.String(128), nullable=False),
        sa.Column("package_version", sa.String(32), nullable=False),
        sa.Column("ontology_version", sa.String(32), nullable=False),
        sa.Column("parent_class_key", sa.String(196), sa.ForeignKey("ontology_class.ontology_class_key")),
        sa.Column("class_kind", sa.String(32), nullable=False),
        sa.Column("primary_label", sa.String(255), nullable=False),
        sa.Column("labels_json", sa.JSON(), nullable=False),
        sa.Column("knowledge_anchors_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("domain_id", "ontology_class_id", name="uq_ontology_class_domain_local_id"),
    )
    op.create_index("idx_ontology_class_domain_id", "ontology_class", ["domain_id"])
    op.create_index("idx_ontology_class_domain_parent", "ontology_class", ["domain_id", "parent_class_key"])

    op.create_table(
        "ontology_alias",
        sa.Column("alias_id", sa.String(64), primary_key=True),
        sa.Column("ontology_class_key", sa.String(196), sa.ForeignKey("ontology_class.ontology_class_key"), nullable=False),
        sa.Column("domain_id", sa.String(64), nullable=False),
        sa.Column("ontology_class_id", sa.String(128), nullable=False),
        sa.Column("language_code", sa.String(16), nullable=False),
        sa.Column("alias_text", sa.String(512), nullable=False),
        sa.Column("normalized_alias", sa.String(512), nullable=False),
        sa.Column("is_preferred", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "domain_id",
            "ontology_class_id",
            "language_code",
            "normalized_alias",
            name="uq_ontology_alias_lookup",
        ),
    )
    op.create_index("idx_ontology_alias_class_key", "ontology_alias", ["ontology_class_key"])
    op.create_index("idx_ontology_alias_domain_id", "ontology_alias", ["domain_id"])
    op.create_index("idx_ontology_alias_language_lookup", "ontology_alias", ["language_code", "normalized_alias"])

    op.create_table(
        "ontology_mapping",
        sa.Column("mapping_id", sa.String(64), primary_key=True),
        sa.Column("ontology_class_key", sa.String(196), sa.ForeignKey("ontology_class.ontology_class_key"), nullable=False),
        sa.Column("domain_id", sa.String(64), nullable=False),
        sa.Column("ontology_class_id", sa.String(128), nullable=False),
        sa.Column("mapping_system", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("mapping_metadata_json", sa.JSON()),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "domain_id",
            "ontology_class_id",
            "mapping_system",
            "external_id",
            name="uq_ontology_mapping_external_ref",
        ),
    )
    op.create_index("idx_ontology_mapping_class_key", "ontology_mapping", ["ontology_class_key"])
    op.create_index("idx_ontology_mapping_domain_id", "ontology_mapping", ["domain_id"])
    op.create_index("idx_ontology_mapping_lookup", "ontology_mapping", ["mapping_system", "external_id"])


def downgrade() -> None:
    op.drop_table("ontology_mapping")
    op.drop_table("ontology_alias")
    op.drop_table("ontology_class")
