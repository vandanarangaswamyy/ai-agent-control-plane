"""create runtime tables

Revision ID: 202605310002
Revises: 202605310001
Create Date: 2026-05-31 00:02:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202605310002"
down_revision: str | None = "202605310001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("agent_version_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "RUNNING",
                "SUCCESS",
                "FAILED",
                "BLOCKED",
                name="agentrunstatus",
                native_enum=False,
                length=32,
            ),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column(
            "input",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(12, 6), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
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
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_version_id"], ["agent_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_runs_agent_id_created_at", "agent_runs", ["agent_id", "created_at"])
    op.create_index(
        "ix_agent_runs_agent_version_id_created_at",
        "agent_runs",
        ["agent_version_id", "created_at"],
    )
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])
    op.create_index("ix_agent_runs_status_created_at", "agent_runs", ["status", "created_at"])
    op.create_index("ix_agent_runs_trace_id", "agent_runs", ["trace_id"])

    op.create_table(
        "tool_calls",
        sa.Column("agent_run_id", sa.Uuid(), nullable=False),
        sa.Column("tool_name", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "RUNNING",
                "SUCCESS",
                "FAILED",
                "BLOCKED",
                name="toolcallstatus",
                native_enum=False,
                length=32,
            ),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column(
            "input",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("span_id", sa.String(length=64), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tool_calls_agent_run_id_created_at",
        "tool_calls",
        ["agent_run_id", "created_at"],
    )
    op.create_index("ix_tool_calls_status_created_at", "tool_calls", ["status", "created_at"])
    op.create_index("ix_tool_calls_tool_name_created_at", "tool_calls", ["tool_name", "created_at"])
    op.create_index("ix_tool_calls_trace_id", "tool_calls", ["trace_id"])

    op.create_table(
        "traces",
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("span_id", sa.String(length=64), nullable=True),
        sa.Column("parent_span_id", sa.String(length=64), nullable=True),
        sa.Column(
            "event_type",
            sa.Enum(
                "AGENT_RUN",
                "TOOL_CALL",
                name="traceeventtype",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(length=255), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "attributes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_traces_entity_type_entity_id", "traces", ["entity_type", "entity_id"])
    op.create_index("ix_traces_event_type_timestamp", "traces", ["event_type", "timestamp"])
    op.create_index("ix_traces_trace_id", "traces", ["trace_id"])


def downgrade() -> None:
    op.drop_index("ix_traces_trace_id", table_name="traces")
    op.drop_index("ix_traces_event_type_timestamp", table_name="traces")
    op.drop_index("ix_traces_entity_type_entity_id", table_name="traces")
    op.drop_table("traces")

    op.drop_index("ix_tool_calls_trace_id", table_name="tool_calls")
    op.drop_index("ix_tool_calls_tool_name_created_at", table_name="tool_calls")
    op.drop_index("ix_tool_calls_status_created_at", table_name="tool_calls")
    op.drop_index("ix_tool_calls_agent_run_id_created_at", table_name="tool_calls")
    op.drop_table("tool_calls")

    op.drop_index("ix_agent_runs_trace_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_status_created_at", table_name="agent_runs")
    op.drop_index("ix_agent_runs_status", table_name="agent_runs")
    op.drop_index("ix_agent_runs_agent_version_id_created_at", table_name="agent_runs")
    op.drop_index("ix_agent_runs_agent_id_created_at", table_name="agent_runs")
    op.drop_table("agent_runs")
