from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.runtime import AgentRun, ToolCall
from app.domain.enums import ApprovalStatus, PolicyDecision

json_payload_type = JSON().with_variant(JSONB, "postgresql")


class ApprovalRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Human approval request for a policy-gated action."""

    __tablename__ = "approval_requests"
    __table_args__ = (
        Index("ix_approval_requests_status_created_at", "status", "created_at"),
        Index("ix_approval_requests_agent_run_id_created_at", "agent_run_id", "created_at"),
    )

    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=True,
    )
    tool_call_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tool_calls.id", ondelete="CASCADE"),
        nullable=True,
    )
    policy_decision: Mapped[PolicyDecision] = mapped_column(
        SQLAlchemyEnum(
            PolicyDecision,
            values_callable=lambda decision: [state.value for state in decision],
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=PolicyDecision.REQUIRE_APPROVAL,
        server_default=PolicyDecision.REQUIRE_APPROVAL.value,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_action: Mapped[dict[str, object]] = mapped_column(
        json_payload_type,
        nullable=False,
        default=dict,
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        SQLAlchemyEnum(
            ApprovalStatus,
            values_callable=lambda status: [state.value for state in status],
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=ApprovalStatus.PENDING,
        server_default=ApprovalStatus.PENDING.value,
    )
    requested_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    agent_run: Mapped[AgentRun | None] = relationship()
    tool_call: Mapped[ToolCall | None] = relationship()

    def mark_reviewed(self, *, status: ApprovalStatus, reviewed_by: str | None) -> None:
        self.status = status
        self.reviewed_by = reviewed_by
        self.reviewed_at = datetime.now(UTC)
