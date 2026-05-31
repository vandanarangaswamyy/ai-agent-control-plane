from __future__ import annotations

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.domain.enums import AgentVersionLifecycle
from app.domain.errors import BusinessRuleViolationError, InvalidStateTransitionError
from app.repositories.agents import AgentRepository
from app.services.agent_registry import AgentRegistryService


def build_service(session: Session) -> AgentRegistryService:
    repository = AgentRepository(session=session)
    return AgentRegistryService(session=session, repository=repository)


def test_service_rejects_empty_version_update(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        service = build_service(session)
        agent = service.create_agent(name="agent", description=None, owner=None)
        version = service.create_version(
            agent_id=agent.id,
            name="draft",
            prompt="Do work",
            model="claude-sonnet-4",
            tool_config={},
            runtime_config={},
        )

        with pytest.raises(BusinessRuleViolationError):
            service.update_draft_version(agent_id=agent.id, version_id=version.id, update_fields={})


def test_service_rejects_deprecating_production_version(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        service = build_service(session)
        agent = service.create_agent(name="agent", description=None, owner=None)
        version = service.create_version(
            agent_id=agent.id,
            name="draft",
            prompt="Do work",
            model="claude-sonnet-4",
            tool_config={},
            runtime_config={},
        )
        version.lifecycle = AgentVersionLifecycle.PRODUCTION
        session.commit()

        with pytest.raises(InvalidStateTransitionError):
            service.deprecate_version(agent_id=agent.id, version_id=version.id)
