from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models.agent import AgentVersion
from app.db.models.deployment import DeploymentEvent
from app.domain.enums import AgentVersionLifecycle, DeploymentEventType


class DeploymentRepository:
    """Persistence operations for deployment lifecycle events."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_event(
        self,
        *,
        agent_id: uuid.UUID,
        event_type: DeploymentEventType,
        source_version_id: uuid.UUID | None,
        target_version_id: uuid.UUID | None,
        reason: str | None,
        trace_id: str,
    ) -> DeploymentEvent:
        event = DeploymentEvent(
            agent_id=agent_id,
            event_type=event_type,
            source_version_id=source_version_id,
            target_version_id=target_version_id,
            reason=reason,
            trace_id=trace_id,
        )
        self._session.add(event)
        self._session.flush()
        return event

    def list_events_for_agent(self, agent_id: uuid.UUID) -> list[DeploymentEvent]:
        statement: Select[tuple[DeploymentEvent]] = (
            select(DeploymentEvent)
            .where(DeploymentEvent.agent_id == agent_id)
            .order_by(DeploymentEvent.created_at.asc(), DeploymentEvent.id.asc())
        )
        return list(self._session.scalars(statement).all())

    def list_promote_events_for_agent(self, agent_id: uuid.UUID) -> list[DeploymentEvent]:
        statement: Select[tuple[DeploymentEvent]] = (
            select(DeploymentEvent)
            .where(
                DeploymentEvent.agent_id == agent_id,
                DeploymentEvent.event_type == DeploymentEventType.PROMOTE,
            )
            .order_by(DeploymentEvent.created_at.desc(), DeploymentEvent.id.desc())
        )
        return list(self._session.scalars(statement).all())

    def get_current_production_version(self, agent_id: uuid.UUID) -> AgentVersion | None:
        statement = select(AgentVersion).where(
            AgentVersion.agent_id == agent_id,
            AgentVersion.lifecycle == AgentVersionLifecycle.PRODUCTION,
        )
        return self._session.scalars(statement).one_or_none()

    def flush(self) -> None:
        self._session.flush()
