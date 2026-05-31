from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.runtime import AgentRun, ToolCall, Trace
from app.domain.enums import AgentRunStatus, ToolCallStatus


def create_agent(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "runtime-agent",
            "description": "Runtime test agent",
            "owner": "platform",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_agent_version(client: TestClient, *, agent_id: str) -> dict[str, object]:
    response = client.post(
        f"/api/v1/agents/{agent_id}/versions",
        json={
            "name": "runtime-v1",
            "prompt": "Use the configured runtime tool",
            "model": "claude-sonnet-4",
            "tool_config": {"default_tool": "browser"},
            "runtime_config": {"temperature": 0},
        },
    )
    assert response.status_code == 201
    return response.json()


def test_successful_run_execution_persists_tool_call_and_traces(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    agent = create_agent(client)
    version = create_agent_version(client, agent_id=str(agent["id"]))

    response = client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": version["id"],
            "task": "Read a document and summarize it",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == AgentRunStatus.SUCCESS
    assert body["start_time"] is not None
    assert body["end_time"] is not None
    assert body["latency_ms"] is not None
    assert body["token_count"] > 0
    assert body["estimated_cost"] == "0.000000"
    assert body["output"]["tool"] == "browser"

    with db_session_factory() as session:
        tool_calls = session.scalars(select(ToolCall)).all()
        traces = session.scalars(select(Trace).order_by(Trace.timestamp)).all()

    assert len(tool_calls) == 1
    assert tool_calls[0].status == ToolCallStatus.SUCCESS
    assert tool_calls[0].latency_ms is not None
    assert {trace.name for trace in traces} >= {
        "AgentRunStarted",
        "AgentRunCompleted",
        "ToolInvoked",
        "ToolSucceeded",
    }


def test_failed_run_execution_persists_failure_details(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    agent = create_agent(client)
    version = create_agent_version(client, agent_id=str(agent["id"]))

    response = client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": version["id"],
            "task": "Trigger a tool failure",
            "tool_name": "browser",
            "tool_input": {"query": "fail-tool"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == AgentRunStatus.FAILED
    assert body["error_message"] == "browser mock failed"
    assert body["end_time"] is not None
    assert body["latency_ms"] is not None

    with db_session_factory() as session:
        tool_call = session.scalars(select(ToolCall)).one()
        trace_names = {trace.name for trace in session.scalars(select(Trace)).all()}

    assert tool_call.status == ToolCallStatus.FAILED
    assert tool_call.error_message == "browser mock failed"
    assert "ToolFailed" in trace_names
    assert "AgentRunFailed" in trace_names


def test_async_run_creation_leaves_run_pending(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
    monkeypatch,
) -> None:
    agent = create_agent(client)
    version = create_agent_version(client, agent_id=str(agent["id"]))
    dispatched: list[str] = []

    class FakeTask:
        @staticmethod
        def delay(run_id: str) -> None:
            dispatched.append(run_id)

    monkeypatch.setattr("app.api.v1.runs.execute_agent_run", FakeTask)

    response = client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": version["id"],
            "task": "Run later",
            "execute_async": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == AgentRunStatus.PENDING
    assert dispatched == [body["id"]]

    with db_session_factory() as session:
        run = session.get(AgentRun, uuid.UUID(body["id"]))
        assert run is not None
        assert run.status == AgentRunStatus.PENDING


def test_list_and_get_runs(client: TestClient) -> None:
    agent = create_agent(client)
    version = create_agent_version(client, agent_id=str(agent["id"]))
    created = client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": version["id"],
            "task": "List me",
        },
    ).json()

    list_response = client.get("/api/v1/runs")
    get_response = client.get(f"/api/v1/runs/{created['id']}")

    assert list_response.status_code == 200
    assert [run["id"] for run in list_response.json()] == [created["id"]]
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]
