from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from tests.api.test_runs import create_agent, create_agent_version


def test_trace_lookup_returns_ordered_events(client: TestClient) -> None:
    agent = create_agent(client)
    version = create_agent_version(client, agent_id=str(agent["id"]))

    run = client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": version["id"],
            "task": "Inspect trace ordering",
        },
    ).json()

    response = client.get(f"/api/v1/traces/{run['trace_id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["trace_id"] == run["trace_id"]
    events = body["events"]
    timestamps = [event["timestamp"] for event in events]
    assert timestamps == sorted(timestamps)
    assert {event["name"] for event in events} >= {
        "AgentRunStarted",
        "AgentRunCompleted",
        "ToolInvoked",
        "ToolSucceeded",
    }


def test_run_timeline_is_chronological_and_includes_approval_flow(client: TestClient) -> None:
    agent = create_agent(client)
    version = create_agent_version(client, agent_id=str(agent["id"]))

    run = client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": version["id"],
            "task": "Approve this email tool call",
            "tool_name": "email",
            "tool_input": {"subject": "Approve this"},
        },
    ).json()

    approvals = client.get("/api/v1/approvals").json()
    assert len(approvals) == 1

    approval_response = client.post(
        f"/api/v1/approvals/{approvals[0]['id']}/approve",
        json={"reviewed_by": "ops"},
    )
    assert approval_response.status_code == 200

    response = client.get(f"/api/v1/runs/{run['id']}/timeline")
    assert response.status_code == 200
    body = response.json()
    events = body["events"]
    timestamps = [event["timestamp"] for event in events]
    assert timestamps == sorted(timestamps)

    names = [event["name"] for event in events]
    assert (
        names.index("PolicyCheck")
        < names.index("ApprovalRequested")
        < names.index("ToolBlocked")
    )
    assert (
        names.index("ApprovalApproved")
        < names.index("ToolInvoked")
        < names.index("ToolSucceeded")
    )
    assert names[-1] == "AgentRunCompleted"


def test_run_failures_reports_denied_tool_call(client: TestClient) -> None:
    agent = create_agent(client)
    version = create_agent_version(client, agent_id=str(agent["id"]))

    run = client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": version["id"],
            "task": "Deny this tool call",
            "tool_name": "browser",
            "tool_input": {"deny": True, "query": "blocked"},
        },
    ).json()

    response = client.get(f"/api/v1/runs/{run['id']}/failures")
    assert response.status_code == 200
    body = response.json()
    assert body["run"]["id"] == run["id"]
    assert body["runtime_error_message"] == "tool input requested denial"
    assert len(body["blocked_tool_calls"]) == 1
    assert len(body["denied_policy_checks"]) == 1
    assert {event["name"] for event in body["trace_events"]} == {"PolicyCheck", "ToolBlocked"}


def test_missing_trace_returns_404(client: TestClient) -> None:
    response = client.get(f"/api/v1/traces/{uuid.uuid4()}")
    assert response.status_code == 404


def test_missing_run_returns_404_for_timeline_and_failures(client: TestClient) -> None:
    run_id = uuid.uuid4()

    timeline_response = client.get(f"/api/v1/runs/{run_id}/timeline")
    failures_response = client.get(f"/api/v1/runs/{run_id}/failures")

    assert timeline_response.status_code == 404
    assert failures_response.status_code == 404


def test_metrics_endpoint_exposes_prometheus_counters(client: TestClient) -> None:
    agent = create_agent(client)
    version = create_agent_version(client, agent_id=str(agent["id"]))

    client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": version["id"],
            "task": "Metric run",
        },
    )
    client.post(
        "/api/v1/runs",
        json={
            "agent_version_id": version["id"],
            "task": "Metric approval run",
            "tool_name": "email",
            "tool_input": {"subject": "Metric approval"},
        },
    ).json()

    approvals = client.get("/api/v1/approvals").json()
    client.post(f"/api/v1/approvals/{approvals[0]['id']}/approve", json={"reviewed_by": "metrics"})

    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "agent_runs_total" in body
    assert "agent_runs_success_total" in body
    assert "agent_runs_blocked_total" in body
    assert "tool_calls_total" in body
    assert "approval_requests_total" in body
    assert "approval_requests_approved_total" in body
    assert "agent_run_latency_seconds_count" in body
    assert "tool_call_latency_seconds_count" in body
