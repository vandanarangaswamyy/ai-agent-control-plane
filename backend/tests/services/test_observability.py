from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.core.telemetry import get_finished_spans
from app.domain.enums import AgentRunStatus
from app.repositories.agents import AgentRepository
from app.repositories.approvals import ApprovalRepository
from app.repositories.runtime import RuntimeRepository
from app.services.agent_registry import AgentRegistryService
from app.services.policy import PolicyEngine
from app.services.runtime import RuntimeService
from app.services.safety_gateway import SafetyGateway
from app.tools.registry import ToolRegistry
from app.workers import tasks


def _create_agent_version(session: Session):
    agent_service = AgentRegistryService(
        session=session,
        repository=AgentRepository(session=session),
    )
    agent = agent_service.create_agent(name="observability-agent", description=None, owner=None)
    return agent_service.create_version(
        agent_id=agent.id,
        name="observability",
        prompt="Use observability",
        model="claude-sonnet-4",
        tool_config={"default_tool": "browser"},
        runtime_config={},
    )


def _build_runtime_service(session: Session) -> RuntimeService:
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


def test_http_and_runtime_spans_are_emitted(
    client,
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        version = _create_agent_version(session)

    response = client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": str(version.id),
            "task": "Emit spans",
        },
    )

    assert response.status_code == 201
    span_names = [span.name for span in get_finished_spans()]
    assert "HTTP POST /api/v1/runs" in span_names
    assert "runtime.execute_run" in span_names
    assert "safety_gateway.invoke_tool" in span_names
    assert "safety_gateway.policy_check" in span_names
    assert "safety_gateway.execute_approved_tool" in span_names
    assert "tool.execute" in span_names


def test_celery_task_span_is_emitted(
    db_session_factory: sessionmaker[Session],
    monkeypatch,
) -> None:
    with db_session_factory() as session:
        version = _create_agent_version(session)
        service = _build_runtime_service(session)
        run = service.create_run(agent_version_id=version.id, task="Execute with celery task")

    monkeypatch.setattr(tasks, "SessionLocal", db_session_factory)

    result = tasks.execute_agent_run(str(run.id))

    assert result == {"run_id": str(run.id), "status": AgentRunStatus.SUCCESS.value}

    span_names = [span.name for span in get_finished_spans()]
    assert "celery.execute_agent_run" in span_names
    assert "runtime.execute_run" in span_names
    assert "tool.execute" in span_names
