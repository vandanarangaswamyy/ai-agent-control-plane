"""create approval requests

Revision ID: 202605310003
Revises: 202605310002
Create Date: 2026-05-31 00:03:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202605310003"
down_revision: str | None = "202605310002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("agent_run_id", sa.Uuid(), nullable=True),
        sa.Column("tool_call_id", sa.Uuid(), nullable=True),
        sa.Column(
            "policy_decision",
            sa.Enum(
                "ALLOW",
                "REQUIRE_APPROVAL",
                "DENY",
                name="policydecision",
                native_enum=False,
                length=32,
            ),
            server_default="REQUIRE_APPROVAL",
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "requested_action",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "APPROVED",
                "REJECTED",
                "EXPIRED",
                name="approvalstatus",
                native_enum=False,
                length=32,
            ),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("requested_by", sa.String(length=255), nullable=True),
        sa.Column("reviewed_by", sa.String(length=255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_call_id"], ["tool_calls.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_approval_requests_agent_run_id_created_at",
        "approval_requests",
        ["agent_run_id", "created_at"],
    )
    op.create_index(
        "ix_approval_requests_status_created_at",
        "approval_requests",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_approval_requests_status_created_at", table_name="approval_requests")
    op.drop_index("ix_approval_requests_agent_run_id_created_at", table_name="approval_requests")
    op.drop_table("approval_requests")
