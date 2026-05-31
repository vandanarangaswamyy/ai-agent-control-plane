"""create deployment events

Revision ID: 202605310005
Revises: 202605310004
Create Date: 2026-05-31 03:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "202605310005"
down_revision: str | None = "202605310004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_agent_versions_agent_id_production",
        "agent_versions",
        ["agent_id"],
        unique=True,
        postgresql_where=sa.text("lifecycle = 'PRODUCTION'"),
        sqlite_where=sa.text("lifecycle = 'PRODUCTION'"),
    )
    op.create_table(
        "deployment_events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("agent_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "PROMOTE",
                "ROLLBACK",
                "DEPRECATE",
                name="deploymenteventtype",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("source_version_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("target_version_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_version_id"], ["agent_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_version_id"], ["agent_versions.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_deployment_events_agent_id_created_at",
        "deployment_events",
        ["agent_id", "created_at"],
    )
    op.create_index(
        "ix_deployment_events_event_type_created_at",
        "deployment_events",
        ["event_type", "created_at"],
    )
    op.create_index(
        "ix_deployment_events_source_version_id",
        "deployment_events",
        ["source_version_id"],
    )
    op.create_index(
        "ix_deployment_events_target_version_id",
        "deployment_events",
        ["target_version_id"],
    )
    op.create_index("ix_deployment_events_trace_id", "deployment_events", ["trace_id"])


def downgrade() -> None:
    op.drop_index("ix_deployment_events_trace_id", table_name="deployment_events")
    op.drop_index("ix_deployment_events_target_version_id", table_name="deployment_events")
    op.drop_index("ix_deployment_events_source_version_id", table_name="deployment_events")
    op.drop_index("ix_deployment_events_event_type_created_at", table_name="deployment_events")
    op.drop_index("ix_deployment_events_agent_id_created_at", table_name="deployment_events")
    op.drop_table("deployment_events")
    op.drop_index("uq_agent_versions_agent_id_production", table_name="agent_versions")
