"""create evaluations tables

Revision ID: 202605310004
Revises: 202605310003
Create Date: 2026-05-31 02:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "202605310004"
down_revision: str | None = "202605310003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

json_type = sa.JSON().with_variant(postgresql.JSONB, "postgresql")


def upgrade() -> None:
    op.create_table(
        "evaluations",
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
        sa.Column("agent_version_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("suite_name", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "RUNNING",
                "PASSED",
                "FAILED",
                name="evaluationstatus",
                native_enum=False,
                length=32,
            ),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("total_cases", sa.Integer(), nullable=True),
        sa.Column("passed_cases", sa.Integer(), nullable=True),
        sa.Column("failed_cases", sa.Integer(), nullable=True),
        sa.Column("success_rate", sa.Numeric(8, 6), nullable=True),
        sa.Column("tool_accuracy", sa.Numeric(8, 6), nullable=True),
        sa.Column("average_latency_ms", sa.Integer(), nullable=True),
        sa.Column("total_cost", sa.Numeric(12, 6), nullable=True),
        sa.Column("failure_rate", sa.Numeric(8, 6), nullable=True),
        sa.Column("report", json_type, nullable=True),
        sa.ForeignKeyConstraint(["agent_version_id"], ["agent_versions.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_evaluations_agent_version_id_created_at",
        "evaluations",
        ["agent_version_id", "created_at"],
    )
    op.create_index(
        "ix_evaluations_suite_name_created_at", "evaluations", ["suite_name", "created_at"]
    )
    op.create_index("ix_evaluations_status_created_at", "evaluations", ["status", "created_at"])
    op.create_index("ix_evaluations_agent_version_id", "evaluations", ["agent_version_id"])
    op.create_index("ix_evaluations_status", "evaluations", ["status"])
    op.create_index("ix_evaluations_trace_id", "evaluations", ["trace_id"])

    op.create_table(
        "evaluation_results",
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
        sa.Column("evaluation_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_name", sa.String(length=255), nullable=False),
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PASSED",
                "FAILED",
                name="evaluationresultstatus",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("run_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("tool_call_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("expected_tool_name", sa.String(length=255), nullable=True),
        sa.Column("actual_tool_name", sa.String(length=255), nullable=True),
        sa.Column("output", json_type, nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(12, 6), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tool_call_id"], ["tool_calls.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_evaluation_results_evaluation_id_created_at",
        "evaluation_results",
        ["evaluation_id", "created_at"],
    )
    op.create_index(
        "ix_evaluation_results_status_created_at",
        "evaluation_results",
        ["status", "created_at"],
    )
    op.create_index("ix_evaluation_results_evaluation_id", "evaluation_results", ["evaluation_id"])
    op.create_index("ix_evaluation_results_status", "evaluation_results", ["status"])
    op.create_index("ix_evaluation_results_run_id", "evaluation_results", ["run_id"])
    op.create_index("ix_evaluation_results_tool_call_id", "evaluation_results", ["tool_call_id"])
    op.create_index("ix_evaluation_results_trace_id", "evaluation_results", ["trace_id"])


def downgrade() -> None:
    op.drop_index("ix_evaluation_results_trace_id", table_name="evaluation_results")
    op.drop_index("ix_evaluation_results_tool_call_id", table_name="evaluation_results")
    op.drop_index("ix_evaluation_results_run_id", table_name="evaluation_results")
    op.drop_index("ix_evaluation_results_status", table_name="evaluation_results")
    op.drop_index("ix_evaluation_results_evaluation_id", table_name="evaluation_results")
    op.drop_index("ix_evaluation_results_status_created_at", table_name="evaluation_results")
    op.drop_index("ix_evaluation_results_evaluation_id_created_at", table_name="evaluation_results")
    op.drop_table("evaluation_results")

    op.drop_index("ix_evaluations_trace_id", table_name="evaluations")
    op.drop_index("ix_evaluations_status", table_name="evaluations")
    op.drop_index("ix_evaluations_agent_version_id", table_name="evaluations")
    op.drop_index("ix_evaluations_status_created_at", table_name="evaluations")
    op.drop_index("ix_evaluations_suite_name_created_at", table_name="evaluations")
    op.drop_index("ix_evaluations_agent_version_id_created_at", table_name="evaluations")
    op.drop_table("evaluations")
