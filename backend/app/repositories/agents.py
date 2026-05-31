from __future__ import annotations

import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.db.models.agent import Agent, AgentVersion


class AgentRepository:
    """Persistence operations for agents and agent versions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_agent(
        self,
        *,
        name: str,
        description: str | None,
        owner: str | None,
    ) -> Agent:
        agent = Agent(name=name, description=description, owner=owner)
        self._session.add(agent)
        self._session.flush()
        return agent

    def list_agents(self, *, limit: int, offset: int) -> list[Agent]:
        statement: Select[tuple[Agent]] = (
            select(Agent)
            .order_by(Agent.created_at.desc(), Agent.name.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(statement).all())

    def get_agent(self, agent_id: uuid.UUID) -> Agent | None:
        return self._session.get(Agent, agent_id)

    def get_agent_by_name_case_insensitive(self, name: str) -> Agent | None:
        statement = select(Agent).where(func.lower(Agent.name) == name.lower())
        return self._session.scalars(statement).one_or_none()

    def get_agent_for_update(self, agent_id: uuid.UUID) -> Agent | None:
        statement = select(Agent).where(Agent.id == agent_id).with_for_update()
        return self._session.scalars(statement).one_or_none()

    def create_version(
        self,
        *,
        agent_id: uuid.UUID,
        version: int,
        name: str | None,
        prompt: str,
        model: str,
        tool_config: dict[str, object],
        runtime_config: dict[str, object],
    ) -> AgentVersion:
        agent_version = AgentVersion(
            agent_id=agent_id,
            version=version,
            name=name,
            prompt=prompt,
            model=model,
            tool_config=tool_config,
            runtime_config=runtime_config,
        )
        self._session.add(agent_version)
        self._session.flush()
        return agent_version

    def get_next_version_number(self, agent_id: uuid.UUID) -> int:
        statement = select(func.coalesce(func.max(AgentVersion.version), 0) + 1).where(
            AgentVersion.agent_id == agent_id
        )
        return int(self._session.scalar(statement) or 1)

    def list_versions(self, *, agent_id: uuid.UUID, limit: int, offset: int) -> list[AgentVersion]:
        statement: Select[tuple[AgentVersion]] = (
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent_id)
            .order_by(AgentVersion.version.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(statement).all())

    def get_version_for_agent(
        self,
        *,
        agent_id: uuid.UUID,
        version_id: uuid.UUID,
    ) -> AgentVersion | None:
        statement = select(AgentVersion).where(
            AgentVersion.id == version_id,
            AgentVersion.agent_id == agent_id,
        )
        return self._session.scalars(statement).one_or_none()

    def flush(self) -> None:
        self._session.flush()
