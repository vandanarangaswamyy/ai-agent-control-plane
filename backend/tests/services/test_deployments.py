from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.agent import Agent, AgentVersion
from app.db.models.deployment import DeploymentEvent
from app.db.models.evaluation import Evaluation
from app.db.models.runtime import Trace
from app.domain.enums import AgentVersionLifecycle, DeploymentEventType, EvaluationStatus
from app.domain.errors import BusinessRuleViolationError
from app.repositories.agents import AgentRepository
from app.repositories.deployments import DeploymentRepository
from app.repositories.evaluations import EvaluationRepository
from app.repositories.runtime import RuntimeRepository
from app.services.agent_registry import AgentRegistryService
from app.services.deployments import DeploymentService


def _create_agent(session: Session, *, name: str) -> Agent:
    agent_service = AgentRegistryService(
        session=session,
        repository=AgentRepository(session=session),
    )
    return agent_service.create_agent(
        name=f"{name}-{uuid.uuid4().hex[:8]}",
        description=None,
        owner=None,
    )


def _create_agent_version(
    session: Session,
    *,
    agent: Agent | None = None,
    name: str = "deployment-agent",
) -> AgentVersion:
    agent_service = AgentRegistryService(
        session=session,
        repository=AgentRepository(session=session),
    )
    owner = agent or _create_agent(session, name=name)
    return agent_service.create_version(
        agent_id=owner.id,
        name="production",
        prompt="Deploy me",
        model="claude-sonnet-4",
        tool_config={"default_tool": "browser"},
        runtime_config={},
    )


def _create_completed_evaluation(
    session: Session,
    *,
    version_id: uuid.UUID,
    status: EvaluationStatus = EvaluationStatus.PASSED,
    success_rate: Decimal = Decimal("1.000000"),
) -> Evaluation:
    now = datetime.now(UTC)
    evaluation = Evaluation(
        agent_version_id=version_id,
        suite_name="deployment-suite",
        status=status,
        trace_id=uuid.uuid4().hex,
        started_at=now,
        finished_at=now,
        total_cases=1,
        passed_cases=1 if status == EvaluationStatus.PASSED else 0,
        failed_cases=0 if status == EvaluationStatus.PASSED else 1,
        success_rate=success_rate,
        tool_accuracy=success_rate,
        average_latency_ms=10,
        total_cost=Decimal("0.000100"),
        failure_rate=Decimal("0.000000")
        if status == EvaluationStatus.PASSED
        else Decimal("1.000000"),
        report={"suite": {"name": "deployment-suite"}, "results": []},
    )
    session.add(evaluation)
    session.commit()
    session.refresh(evaluation)
    return evaluation


def _build_deployment_service(
    session: Session,
    *,
    minimum_success_rate: Decimal = Decimal("0.95"),
) -> DeploymentService:
    return DeploymentService(
        session=session,
        agent_repository=AgentRepository(session=session),
        evaluation_repository=EvaluationRepository(session=session),
        deployment_repository=DeploymentRepository(session=session),
        runtime_repository=RuntimeRepository(session=session),
        minimum_success_rate=minimum_success_rate,
    )


def test_successful_promotion_records_history_and_traces(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        version = _create_agent_version(session)
        _create_completed_evaluation(session, version_id=version.id)
        service = _build_deployment_service(session)

        result = service.promote_version(
            agent_id=version.agent_id,
            agent_version_id=version.id,
            reason="ready for production",
        )

        assert result.agent_id == version.agent_id
        assert result.version_promoted == version.id
        assert result.previous_production_version is None

        refreshed_version = session.get(AgentVersion, version.id)
        assert refreshed_version is not None
        assert refreshed_version.lifecycle == AgentVersionLifecycle.PRODUCTION

        events = session.scalars(select(DeploymentEvent)).all()
        assert len(events) == 1
        assert events[0].event_type == DeploymentEventType.PROMOTE

        trace_names = {trace.name for trace in session.scalars(select(Trace)).all()}
        assert "DeploymentPromoted" in trace_names


def test_promotion_denied_without_evaluation(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        version = _create_agent_version(session)
        service = _build_deployment_service(session)

        with pytest.raises(BusinessRuleViolationError):
            service.promote_version(
                agent_id=version.agent_id,
                agent_version_id=version.id,
                reason=None,
            )


def test_promotion_denied_when_latest_evaluation_failed(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        version = _create_agent_version(session)
        _create_completed_evaluation(
            session,
            version_id=version.id,
            status=EvaluationStatus.FAILED,
            success_rate=Decimal("0.000000"),
        )
        service = _build_deployment_service(session)

        with pytest.raises(BusinessRuleViolationError):
            service.promote_version(
                agent_id=version.agent_id,
                agent_version_id=version.id,
                reason=None,
            )


def test_promotion_denied_for_deprecated_version(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        version = _create_agent_version(session)
        _create_completed_evaluation(session, version_id=version.id)
        agent_service = AgentRegistryService(
            session=session,
            repository=AgentRepository(session=session),
        ).with_deployment_repository(DeploymentRepository(session=session))
        agent_service.deprecate_version(agent_id=version.agent_id, version_id=version.id)
        service = _build_deployment_service(session)

        with pytest.raises(BusinessRuleViolationError):
            service.promote_version(
                agent_id=version.agent_id,
                agent_version_id=version.id,
                reason=None,
            )


def test_promotion_enforces_single_production_version(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        agent = _create_agent(session, name="deployment-agent")
        version_one = _create_agent_version(session, agent=agent, name="deployment-agent")
        version_two = _create_agent_version(session, agent=agent, name="deployment-agent")
        _create_completed_evaluation(session, version_id=version_one.id)
        _create_completed_evaluation(session, version_id=version_two.id)
        service = _build_deployment_service(session)

        service.promote_version(
            agent_id=version_one.agent_id,
            agent_version_id=version_one.id,
            reason=None,
        )
        service.promote_version(
            agent_id=version_two.agent_id,
            agent_version_id=version_two.id,
            reason=None,
        )

        production_versions = session.scalars(
            select(AgentVersion).where(
                AgentVersion.agent_id == version_one.agent_id,
                AgentVersion.lifecycle == AgentVersionLifecycle.PRODUCTION,
            )
        ).all()
        assert len(production_versions) == 1
        assert production_versions[0].id == version_two.id
        first_version = session.get(AgentVersion, version_one.id)
        assert first_version is not None
        assert first_version.lifecycle == AgentVersionLifecycle.APPROVED


def test_rollback_restores_previous_version_and_records_trace(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        agent = _create_agent(session, name="rollback-agent")
        version_one = _create_agent_version(session, agent=agent, name="rollback-agent")
        version_two = _create_agent_version(session, agent=agent, name="rollback-agent")
        _create_completed_evaluation(session, version_id=version_one.id)
        _create_completed_evaluation(session, version_id=version_two.id)
        service = _build_deployment_service(session)

        service.promote_version(
            agent_id=version_one.agent_id,
            agent_version_id=version_one.id,
            reason=None,
        )
        service.promote_version(
            agent_id=version_one.agent_id,
            agent_version_id=version_two.id,
            reason=None,
        )

        result = service.rollback(agent_id=version_one.agent_id, reason="revert")

        assert result.agent_id == version_one.agent_id
        assert result.version_restored == version_one.id

        restored_version = session.get(AgentVersion, version_one.id)
        current_version = session.get(AgentVersion, version_two.id)
        assert restored_version is not None
        assert current_version is not None
        assert restored_version.lifecycle == AgentVersionLifecycle.PRODUCTION
        assert current_version.lifecycle == AgentVersionLifecycle.APPROVED

        trace_names = {trace.name for trace in session.scalars(select(Trace)).all()}
        assert "DeploymentRolledBack" in trace_names


def test_deployment_history_returns_ordered_events(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        agent = _create_agent(session, name="history-agent")
        version_one = _create_agent_version(session, agent=agent, name="history-agent")
        version_two = _create_agent_version(session, agent=agent, name="history-agent")
        version_three = _create_agent_version(session, agent=agent, name="history-agent")
        _create_completed_evaluation(session, version_id=version_one.id)
        _create_completed_evaluation(session, version_id=version_two.id)
        _create_completed_evaluation(session, version_id=version_three.id)
        agent_service = AgentRegistryService(
            session=session,
            repository=AgentRepository(session=session),
        ).with_deployment_repository(DeploymentRepository(session=session))
        service = _build_deployment_service(session)

        service.promote_version(
            agent_id=agent.id,
            agent_version_id=version_one.id,
            reason="first release",
        )
        agent_service.deprecate_version(agent_id=agent.id, version_id=version_two.id)
        service.promote_version(
            agent_id=agent.id,
            agent_version_id=version_three.id,
            reason="second release",
        )

        events = service.list_deployment_events(agent_id=agent.id)
        assert [event.event_type for event in events] == [
            DeploymentEventType.PROMOTE,
            DeploymentEventType.DEPRECATE,
            DeploymentEventType.PROMOTE,
        ]
