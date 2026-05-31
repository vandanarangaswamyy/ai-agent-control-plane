from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.agent import AgentVersion
from app.db.models.runtime import AgentRun, ToolCall
from app.domain.enums import EvaluationResultStatus, EvaluationStatus

json_report_type = JSON().with_variant(JSONB, "postgresql")


class Evaluation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Execution of an evaluation suite against a specific agent version."""

    __tablename__ = "evaluations"
    __table_args__ = (
        Index("ix_evaluations_agent_version_id_created_at", "agent_version_id", "created_at"),
        Index("ix_evaluations_suite_name_created_at", "suite_name", "created_at"),
        Index("ix_evaluations_status_created_at", "status", "created_at"),
    )

    agent_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    suite_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[EvaluationStatus] = mapped_column(
        SQLAlchemyEnum(
            EvaluationStatus,
            values_callable=lambda status: [state.value for state in status],
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=EvaluationStatus.PENDING,
        server_default=EvaluationStatus.PENDING.value,
        index=True,
    )
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_cases: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passed_cases: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failed_cases: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), nullable=True)
    tool_accuracy: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), nullable=True)
    average_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    failure_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), nullable=True)
    report: Mapped[dict[str, object] | None] = mapped_column(json_report_type, nullable=True)

    agent_version: Mapped[AgentVersion] = relationship()
    results: Mapped[list[EvaluationResult]] = relationship(
        back_populates="evaluation",
        cascade="all, delete-orphan",
        order_by="EvaluationResult.created_at",
    )


class EvaluationResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Per-case outcome produced by an evaluation run."""

    __tablename__ = "evaluation_results"
    __table_args__ = (
        Index("ix_evaluation_results_evaluation_id_created_at", "evaluation_id", "created_at"),
        Index("ix_evaluation_results_status_created_at", "status", "created_at"),
    )

    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[EvaluationResultStatus] = mapped_column(
        SQLAlchemyEnum(
            EvaluationResultStatus,
            values_callable=lambda status: [state.value for state in status],
            native_enum=False,
            length=32,
        ),
        nullable=False,
        index=True,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tool_call_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tool_calls.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    expected_tool_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actual_tool_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    output: Mapped[dict[str, object] | None] = mapped_column(json_report_type, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    evaluation: Mapped[Evaluation] = relationship(back_populates="results")
    run: Mapped[AgentRun | None] = relationship()
    tool_call: Mapped[ToolCall | None] = relationship()
