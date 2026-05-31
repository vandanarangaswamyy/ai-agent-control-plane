from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.agent import Agent, AgentVersion
from app.domain.enums import AgentVersionLifecycle, DeploymentEventType
from app.domain.errors import (
    BusinessRuleViolationError,
    ConflictError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.repositories.agents import AgentRepository
from app.repositories.deployments import DeploymentRepository


class AgentRegistryService:
    """Business operations for the Agent Registry."""

    _editable_version_fields = {"name", "prompt", "model", "tool_config", "runtime_config"}
    _deprecatable_lifecycles = {
        AgentVersionLifecycle.DRAFT,
        AgentVersionLifecycle.EVALUATED,
        AgentVersionLifecycle.APPROVED,
    }

    def __init__(self, *, session: Session, repository: AgentRepository) -> None:
        self._session = session
        self._repository = repository
        self._deployment_repository: DeploymentRepository | None = None

    def with_deployment_repository(
        self,
        deployment_repository: DeploymentRepository,
    ) -> AgentRegistryService:
        self._deployment_repository = deployment_repository
        return self

    def create_agent(
        self,
        *,
        name: str,
        description: str | None,
        owner: str | None,
    ) -> Agent:
        existing_agent = self._repository.get_agent_by_name_case_insensitive(name)
        if existing_agent is not None:
            raise ConflictError(f"agent name already exists: {name}")

        try:
            agent = self._repository.create_agent(
                name=name,
                description=description,
                owner=owner,
            )
            self._session.commit()
            self._session.refresh(agent)
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError(f"agent name already exists: {name}") from exc

        return agent

    def list_agents(self, *, limit: int, offset: int) -> list[Agent]:
        return self._repository.list_agents(limit=limit, offset=offset)

    def get_agent(self, agent_id: uuid.UUID) -> Agent:
        agent = self._repository.get_agent(agent_id)
        if agent is None:
            raise NotFoundError("agent not found")
        return agent

    def create_version(
        self,
        *,
        agent_id: uuid.UUID,
        name: str | None,
        prompt: str,
        model: str,
        tool_config: dict[str, object],
        runtime_config: dict[str, object],
    ) -> AgentVersion:
        try:
            agent = self._repository.get_agent_for_update(agent_id)
            if agent is None:
                raise NotFoundError("agent not found")

            version_number = self._repository.get_next_version_number(agent_id)
            agent_version = self._repository.create_version(
                agent_id=agent_id,
                version=version_number,
                name=name,
                prompt=prompt,
                model=model,
                tool_config=tool_config,
                runtime_config=runtime_config,
            )
            self._session.commit()
            self._session.refresh(agent_version)
        except NotFoundError:
            self._session.rollback()
            raise
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError("agent version already exists") from exc

        return agent_version

    def list_versions(self, *, agent_id: uuid.UUID, limit: int, offset: int) -> list[AgentVersion]:
        self.get_agent(agent_id)
        return self._repository.list_versions(agent_id=agent_id, limit=limit, offset=offset)

    def update_draft_version(
        self,
        *,
        agent_id: uuid.UUID,
        version_id: uuid.UUID,
        update_fields: dict[str, object],
    ) -> AgentVersion:
        if not update_fields:
            raise BusinessRuleViolationError("at least one version field must be provided")

        invalid_fields = set(update_fields) - self._editable_version_fields
        if invalid_fields:
            fields = ", ".join(sorted(invalid_fields))
            raise BusinessRuleViolationError(f"unsupported version update fields: {fields}")

        agent_version = self._repository.get_version_for_agent(
            agent_id=agent_id,
            version_id=version_id,
        )
        if agent_version is None:
            raise NotFoundError("agent version not found")

        if agent_version.lifecycle != AgentVersionLifecycle.DRAFT:
            raise BusinessRuleViolationError("only DRAFT versions can be edited")

        for field_name, value in update_fields.items():
            setattr(agent_version, field_name, value)

        self._repository.flush()
        self._session.commit()
        self._session.refresh(agent_version)
        return agent_version

    def deprecate_version(self, *, agent_id: uuid.UUID, version_id: uuid.UUID) -> AgentVersion:
        agent_version = self._repository.get_version_for_agent(
            agent_id=agent_id,
            version_id=version_id,
        )
        if agent_version is None:
            raise NotFoundError("agent version not found")

        if agent_version.lifecycle not in self._deprecatable_lifecycles:
            raise InvalidStateTransitionError(
                f"cannot deprecate version from {agent_version.lifecycle} lifecycle"
            )

        agent_version.lifecycle = AgentVersionLifecycle.DEPRECATED
        self._repository.flush()
        if self._deployment_repository is not None:
            self._deployment_repository.create_event(
                agent_id=agent_id,
                event_type=DeploymentEventType.DEPRECATE,
                source_version_id=agent_version.id,
                target_version_id=None,
                reason="version deprecated",
                trace_id=uuid.uuid4().hex,
            )
        self._session.commit()
        self._session.refresh(agent_version)
        return agent_version
