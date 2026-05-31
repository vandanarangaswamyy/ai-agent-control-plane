from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums import AgentVersionLifecycle

json_config_type = JSON().with_variant(JSONB, "postgresql")


class Agent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Registered agent identity."""

    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (Index("uq_agents_name_lower", func.lower(name), unique=True),)

    versions: Mapped[list[AgentVersion]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
        order_by="AgentVersion.version",
    )


class AgentVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Versioned configuration for a registered agent."""

    __tablename__ = "agent_versions"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_agent_versions_version_positive"),
        UniqueConstraint("agent_id", "version", name="uq_agent_versions_agent_id_version"),
        Index("ix_agent_versions_agent_id_lifecycle", "agent_id", "lifecycle"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    tool_config: Mapped[dict[str, object]] = mapped_column(
        json_config_type,
        nullable=False,
        default=dict,
    )
    runtime_config: Mapped[dict[str, object]] = mapped_column(
        json_config_type,
        nullable=False,
        default=dict,
    )
    lifecycle: Mapped[AgentVersionLifecycle] = mapped_column(
        SQLAlchemyEnum(
            AgentVersionLifecycle,
            values_callable=lambda lifecycle: [state.value for state in lifecycle],
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=AgentVersionLifecycle.DRAFT,
        server_default=AgentVersionLifecycle.DRAFT.value,
        index=True,
    )

    agent: Mapped[Agent] = relationship(back_populates="versions")
