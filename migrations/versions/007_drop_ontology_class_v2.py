"""Drop ontology_class after migration to sw_base_model.

Revision ID: 007
Revises: 006
Create Date: 2026-04-28

This migration is structurally reversible only. Upgrade drops local class
metadata now owned by sw_base_model; downgrade recreates an empty table, but
the dropped data is not restored.
"""

from alembic import op
import sqlalchemy as sa


revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


FK_CONSTRAINTS = (
    ("ontology_alias", "ontology_alias_ontology_class_key_fkey"),
    ("ontology_mapping", "ontology_mapping_ontology_class_key_fkey"),
    ("chunk_ontology_anchor", "chunk_ontology_anchor_ontology_class_key_fkey"),
    ("knowledge_object", "knowledge_object_ontology_class_key_fkey"),
)


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if _is_postgresql():
        for table_name, constraint_name in FK_CONSTRAINTS:
            op.drop_constraint(constraint_name, table_name, type_="foreignkey")
    op.drop_table("ontology_class")


def downgrade() -> None:
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
