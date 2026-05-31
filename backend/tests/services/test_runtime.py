from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.runtime import AgentRun, ToolCall, Trace
from app.domain.enums import AgentRunStatus, ToolCallStatus
from app.repositories.agents import AgentRepository
from app.repositories.approvals import ApprovalRepository
from app.repositories.runtime import RuntimeRepository
from app.services.agent_registry import AgentRegistryService
from app.services.policy import PolicyEngine
from app.services.runtime import RuntimeService
from app.services.safety_gateway import SafetyGateway
from app.tools.registry import ToolRegistry
from app.workers import tasks


def create_agent_version(session: Session):
    agent_service = AgentRegistryService(
        session=session,
        repository=AgentRepository(session=session),
    )
    agent = agent_service.create_agent(name="service-runtime-agent", description=None, owner=None)
    return agent_service.create_version(
        agent_id=agent.id,
        name="runtime",
        prompt="Use runtime",
        model="claude-sonnet-4",
        tool_config={"default_tool": "browser"},
        runtime_config={},
    )


def build_runtime_service(session: Session) -> RuntimeService:
    runtime_repository = RuntimeRepository(session=session)
    safety_gateway = SafetyGateway(
        runtime_repository=runtime_repository,
        approval_repository=ApprovalRepository(session=session),
        tool_registry=ToolRegistry(),
        policy_engine=PolicyEngine(),
    )
    return RuntimeService(
        session=session,
        repository=runtime_repository,
        safety_gateway=safety_gateway,
    )


def test_runtime_state_transitions_and_latency(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        version = create_agent_version(session)
        service = build_runtime_service(session)

        run = service.create_and_execute_run(
            agent_version_id=version.id,
            task="Summarize runtime state",
        )

        assert run.status == AgentRunStatus.SUCCESS
        assert run.start_time is not None
        assert run.end_time is not None
        assert run.latency_ms is not None
        assert run.latency_ms >= 0
        assert run.token_count is not None
        assert run.estimated_cost is not None

        persisted_run = session.get(AgentRun, run.id)
        assert persisted_run is not None
        assert persisted_run.status == AgentRunStatus.SUCCESS


def test_celery_task_executes_shared_runtime_logic(
    db_session_factory: sessionmaker[Session],
    monkeypatch,
) -> None:
    with db_session_factory() as session:
        version = create_agent_version(session)
        service = build_runtime_service(session)
        run = service.create_run(agent_version_id=version.id, task="Execute with celery task")

    monkeypatch.setattr(tasks, "SessionLocal", db_session_factory)

    result = tasks.execute_agent_run(str(run.id))

    assert result == {"run_id": str(run.id), "status": AgentRunStatus.SUCCESS.value}

    with db_session_factory() as session:
        persisted_run = session.get(AgentRun, run.id)
        tool_call = session.scalars(select(ToolCall)).one()
        trace_names = {trace.name for trace in session.scalars(select(Trace)).all()}

    assert persisted_run is not None
    assert persisted_run.status == AgentRunStatus.SUCCESS
    assert tool_call.status == ToolCallStatus.SUCCESS
    assert "AgentRunCompleted" in trace_names
    assert "ToolSucceeded" in trace_names
