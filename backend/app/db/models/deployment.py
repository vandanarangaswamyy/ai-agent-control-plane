from __future__ import annotations

import uuid

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.agent import Agent, AgentVersion
from app.domain.enums import DeploymentEventType


class DeploymentEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persisted deployment lifecycle event for an agent version."""

    __tablename__ = "deployment_events"
    __table_args__ = (
        Index("ix_deployment_events_agent_id_created_at", "agent_id", "created_at"),
        Index("ix_deployment_events_event_type_created_at", "event_type", "created_at"),
        Index("ix_deployment_events_source_version_id", "source_version_id"),
        Index("ix_deployment_events_target_version_id", "target_version_id"),
        Index("ix_deployment_events_trace_id", "trace_id"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[DeploymentEventType] = mapped_column(
        SQLAlchemyEnum(
            DeploymentEventType,
            values_callable=lambda event_type: [event.value for event in event_type],
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    source_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    agent: Mapped[Agent] = relationship()
    source_version: Mapped[AgentVersion | None] = relationship(
        foreign_keys=[source_version_id],
    )
    target_version: Mapped[AgentVersion | None] = relationship(
        foreign_keys=[target_version_id],
    )
