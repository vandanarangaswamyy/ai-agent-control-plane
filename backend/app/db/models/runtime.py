from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.agent import Agent, AgentVersion
from app.domain.enums import AgentRunStatus, ToolCallStatus, TraceEventType

json_payload_type = JSON().with_variant(JSONB, "postgresql")


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Execution record for a specific agent version."""

    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_agent_id_created_at", "agent_id", "created_at"),
        Index("ix_agent_runs_agent_version_id_created_at", "agent_version_id", "created_at"),
        Index("ix_agent_runs_status_created_at", "status", "created_at"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[AgentRunStatus] = mapped_column(
        SQLAlchemyEnum(
            AgentRunStatus,
            values_callable=lambda status: [state.value for state in status],
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=AgentRunStatus.PENDING,
        server_default=AgentRunStatus.PENDING.value,
        index=True,
    )
    input: Mapped[dict[str, object]] = mapped_column(
        json_payload_type,
        nullable=False,
        default=dict,
    )
    output: Mapped[dict[str, object] | None] = mapped_column(json_payload_type, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    agent: Mapped[Agent] = relationship()
    agent_version: Mapped[AgentVersion] = relationship()
    tool_calls: Mapped[list[ToolCall]] = relationship(
        back_populates="agent_run",
        cascade="all, delete-orphan",
        order_by="ToolCall.created_at",
    )


class ToolCall(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Auditable record for one tool invocation."""

    __tablename__ = "tool_calls"
    __table_args__ = (
        Index("ix_tool_calls_agent_run_id_created_at", "agent_run_id", "created_at"),
        Index("ix_tool_calls_tool_name_created_at", "tool_name", "created_at"),
        Index("ix_tool_calls_status_created_at", "status", "created_at"),
    )

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ToolCallStatus] = mapped_column(
        SQLAlchemyEnum(
            ToolCallStatus,
            values_callable=lambda status: [state.value for state in status],
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=ToolCallStatus.PENDING,
        server_default=ToolCallStatus.PENDING.value,
    )
    input: Mapped[dict[str, object]] = mapped_column(
        json_payload_type,
        nullable=False,
        default=dict,
    )
    output: Mapped[dict[str, object] | None] = mapped_column(json_payload_type, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    span_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    agent_run: Mapped[AgentRun] = relationship(back_populates="tool_calls")


class Trace(UUIDPrimaryKeyMixin, Base):
    """Persisted trace event for runtime timelines."""

    __tablename__ = "traces"
    __table_args__ = (
        Index("ix_traces_event_type_timestamp", "event_type", "timestamp"),
        Index("ix_traces_entity_type_entity_id", "entity_type", "entity_id"),
    )

    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    span_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parent_span_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[TraceEventType] = mapped_column(
        SQLAlchemyEnum(
            TraceEventType,
            values_callable=lambda event_type: [event.value for event in event_type],
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    attributes: Mapped[dict[str, object]] = mapped_column(
        json_payload_type,
        nullable=False,
        default=dict,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
