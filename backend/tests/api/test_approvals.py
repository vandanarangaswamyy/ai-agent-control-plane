from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.approval import ApprovalRequest
from app.db.models.runtime import AgentRun, ToolCall, Trace
from app.domain.enums import AgentRunStatus, ApprovalStatus, ToolCallStatus


def create_agent_version(client: TestClient) -> dict[str, object]:
    agent_response = client.post(
        "/api/v1/agents",
        json={
            "name": "safety-agent",
            "description": "Safety test agent",
            "owner": "platform",
        },
    )
    assert agent_response.status_code == 201
    agent = agent_response.json()

    version_response = client.post(
        f"/api/v1/agents/{agent['id']}/versions",
        json={
            "name": "safety-v1",
            "prompt": "Use safe runtime tools",
            "model": "claude-sonnet-4",
            "tool_config": {"default_tool": "browser"},
            "runtime_config": {},
        },
    )
    assert version_response.status_code == 201
    return version_response.json()


def create_blocked_email_run(client: TestClient, *, version_id: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": version_id,
            "task": "Send an approval-gated email",
            "tool_name": "email",
            "tool_input": {"to": "ops@example.com", "subject": "Approval required"},
        },
    )
    assert response.status_code == 201
    return response.json()


def test_allow_path_executes_and_records_policy_trace(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    version = create_agent_version(client)

    response = client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": version["id"],
            "task": "Browse approved path",
            "tool_name": "browser",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == AgentRunStatus.SUCCESS

    with db_session_factory() as session:
        trace_names = {trace.name for trace in session.scalars(select(Trace)).all()}
        approvals = session.scalars(select(ApprovalRequest)).all()

    assert "PolicyCheck" in trace_names
    assert "ToolSucceeded" in trace_names
    assert approvals == []


def test_require_approval_path_blocks_run_and_creates_approval(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    version = create_agent_version(client)

    body = create_blocked_email_run(client, version_id=str(version["id"]))

    assert body["status"] == AgentRunStatus.BLOCKED
    assert body["end_time"] is None

    with db_session_factory() as session:
        approval = session.scalars(select(ApprovalRequest)).one()
        tool_call = session.scalars(select(ToolCall)).one()
        trace_names = {trace.name for trace in session.scalars(select(Trace)).all()}

    assert approval.status == ApprovalStatus.PENDING
    assert approval.reason == "default policy for email: REQUIRE_APPROVAL"
    assert tool_call.status == ToolCallStatus.BLOCKED
    assert trace_names >= {"PolicyCheck", "ApprovalRequested", "ToolBlocked"}


def test_deny_path_blocks_without_creating_approval(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    version = create_agent_version(client)

    response = client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": version["id"],
            "task": "Denied browser action",
            "tool_name": "browser",
            "tool_input": {"query": "blocked", "deny": True},
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == AgentRunStatus.BLOCKED

    with db_session_factory() as session:
        approvals = session.scalars(select(ApprovalRequest)).all()
        tool_call = session.scalars(select(ToolCall)).one()
        trace_names = {trace.name for trace in session.scalars(select(Trace)).all()}

    assert approvals == []
    assert tool_call.status == ToolCallStatus.BLOCKED
    assert trace_names >= {"PolicyCheck", "ToolBlocked"}
    assert "ToolInvoked" not in trace_names


def test_approval_acceptance_resumes_and_completes_run(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    version = create_agent_version(client)
    blocked_run = create_blocked_email_run(client, version_id=str(version["id"]))

    with db_session_factory() as session:
        approval_id = session.scalars(select(ApprovalRequest.id)).one()

    response = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json={"reviewed_by": "reviewer@example.com"},
    )

    assert response.status_code == 200
    approval = response.json()
    assert approval["status"] == ApprovalStatus.APPROVED

    with db_session_factory() as session:
        run = session.get(AgentRun, uuid.UUID(blocked_run["id"]))
        tool_call = session.scalars(select(ToolCall)).one()
        trace_names = {trace.name for trace in session.scalars(select(Trace)).all()}

    assert run is not None
    assert run.status == AgentRunStatus.SUCCESS
    assert run.output is not None
    assert tool_call.status == ToolCallStatus.SUCCESS
    assert trace_names >= {"ApprovalApproved", "ToolInvoked", "ToolSucceeded", "AgentRunCompleted"}


def test_approval_rejection_keeps_run_blocked(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    version = create_agent_version(client)
    blocked_run = create_blocked_email_run(client, version_id=str(version["id"]))

    with db_session_factory() as session:
        approval_id = session.scalars(select(ApprovalRequest.id)).one()

    response = client.post(
        f"/api/v1/approvals/{approval_id}/reject",
        json={"reviewed_by": "reviewer@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == ApprovalStatus.REJECTED

    with db_session_factory() as session:
        run = session.get(AgentRun, uuid.UUID(blocked_run["id"]))
        tool_call = session.scalars(select(ToolCall)).one()
        trace_names = {trace.name for trace in session.scalars(select(Trace)).all()}

    assert run is not None
    assert run.status == AgentRunStatus.BLOCKED
    assert run.error_message == "approval rejected"
    assert tool_call.status == ToolCallStatus.BLOCKED
    assert trace_names >= {"ApprovalRejected", "ToolBlocked"}


def test_approval_endpoints_list_and_get(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    version = create_agent_version(client)
    create_blocked_email_run(client, version_id=str(version["id"]))

    with db_session_factory() as session:
        approval_id = session.scalars(select(ApprovalRequest.id)).one()

    list_response = client.get("/api/v1/approvals")
    get_response = client.get(f"/api/v1/approvals/{approval_id}")

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [str(approval_id)]
    assert get_response.status_code == 200
    assert get_response.json()["id"] == str(approval_id)
