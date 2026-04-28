"""Drop structural ontology mappings now owned by sw_base_model.

Revision ID: 005
Revises: 004
Create Date: 2026-04-28

This migration is intentionally one-way for data. Structural mappings were
exported to sw_base_model before this cut, and KnowFabric should retain only
OEM naming variants in ontology_mapping after the contract migration.
"""

from alembic import op
import sqlalchemy as sa


revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM ontology_mapping
            WHERE mapping_system IN ('brick', '223p', 'open223')
               OR external_id LIKE 'brick:%'
               OR external_id LIKE '223p:%'
               OR external_id LIKE 'open223:%'
               OR CAST(mapping_metadata_json AS TEXT) LIKE '%brick_to_223p%'
               OR CAST(mapping_metadata_json AS TEXT) LIKE '%brick_to_open223%'
               OR CAST(mapping_metadata_json AS TEXT) LIKE '%brick_to_external_standard%'
            """
        )
    )


def downgrade() -> None:
    # Deleted structural mappings cannot be reconstructed from KnowFabric.
    pass
