"""Create KO feedback event table.

Revision ID: 006
Revises: 005
Create Date: 2026-04-28
"""

from alembic import op
import sqlalchemy as sa


revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ko_feedback_event",
        sa.Column("event_id", sa.String(64), primary_key=True),
        sa.Column("event_key", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("project_id", sa.String(64), nullable=False),
        sa.Column("finding_id", sa.String(64)),
        sa.Column("reviewer_id", sa.String(64)),
        sa.Column("knowledge_object_id", sa.String(64)),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("event_key", name="uq_ko_feedback_event_key"),
    )
    op.create_index("idx_ko_feedback_event_type", "ko_feedback_event", ["event_type"])
    op.create_index("idx_ko_feedback_project_id", "ko_feedback_event", ["project_id"])
    op.create_index("idx_ko_feedback_finding_id", "ko_feedback_event", ["finding_id"])
    op.create_index("idx_ko_feedback_knowledge_object_id", "ko_feedback_event", ["knowledge_object_id"])
    op.create_index(
        "idx_ko_feedback_identity",
        "ko_feedback_event",
        ["project_id", "finding_id", "knowledge_object_id", "event_type"],
    )


def downgrade() -> None:
    op.drop_table("ko_feedback_event")
