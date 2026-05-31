from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.evaluation import Evaluation
from app.domain.enums import EvaluationStatus


def _create_agent(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": f"deployment-api-agent-{uuid.uuid4().hex[:8]}",
            "description": "Deployment test agent",
            "owner": "platform",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_version(
    client: TestClient,
    *,
    agent_id: str,
    version_name: str,
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/agents/{agent_id}/versions",
        json={
            "name": version_name,
            "prompt": "Deploy me",
            "model": "claude-sonnet-4",
            "tool_config": {"default_tool": "browser"},
            "runtime_config": {},
        },
    )
    assert response.status_code == 201
    return response.json()


def _seed_evaluation(
    session: Session,
    *,
    version_id: str,
    status: EvaluationStatus = EvaluationStatus.PASSED,
    success_rate: Decimal = Decimal("1.000000"),
) -> None:
    now = datetime.now(UTC)
    evaluation = Evaluation(
        agent_version_id=uuid.UUID(version_id),
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
        average_latency_ms=12,
        total_cost=Decimal("0.000100"),
        failure_rate=Decimal("0.000000")
        if status == EvaluationStatus.PASSED
        else Decimal("1.000000"),
        report={"suite": {"name": "deployment-suite"}, "results": []},
    )
    session.add(evaluation)
    session.commit()


def test_promotion_endpoint_succeeds_and_history_is_returned(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    agent = _create_agent(client)
    version = _create_version(client, agent_id=str(agent["id"]), version_name="prod")

    with db_session_factory() as session:
        _seed_evaluation(session, version_id=str(version["id"]))

    response = client.post(
        "/api/v1/deployments/promote",
        json={
            "agent_id": agent["id"],
            "agent_version_id": version["id"],
            "reason": "ready for production",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["agent_id"] == agent["id"]
    assert body["version_promoted"] == version["id"]
    assert body["previous_production_version"] is None

    history_response = client.get(f"/api/v1/agents/{agent['id']}/deployments")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 1
    assert history[0]["event_type"] == "PROMOTE"


def test_promotion_endpoint_denies_missing_evaluation(
    client: TestClient,
) -> None:
    agent = _create_agent(client)
    version = _create_version(client, agent_id=str(agent["id"]), version_name="draft")

    response = client.post(
        "/api/v1/deployments/promote",
        json={
            "agent_id": agent["id"],
            "agent_version_id": version["id"],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "BusinessRuleViolationError"


def test_rollback_endpoint_restores_previous_version(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    agent = _create_agent(client)
    version_one = _create_version(client, agent_id=str(agent["id"]), version_name="v1")
    version_two = _create_version(client, agent_id=str(agent["id"]), version_name="v2")

    with db_session_factory() as session:
        _seed_evaluation(session, version_id=str(version_one["id"]))
        _seed_evaluation(session, version_id=str(version_two["id"]))

    promote_one = client.post(
        "/api/v1/deployments/promote",
        json={
            "agent_id": agent["id"],
            "agent_version_id": version_one["id"],
        },
    )
    promote_two = client.post(
        "/api/v1/deployments/promote",
        json={
            "agent_id": agent["id"],
            "agent_version_id": version_two["id"],
        },
    )
    assert promote_one.status_code == 201
    assert promote_two.status_code == 201

    rollback_response = client.post(
        "/api/v1/deployments/rollback",
        json={
            "agent_id": agent["id"],
            "reason": "rollback test",
        },
    )

    assert rollback_response.status_code == 200
    body = rollback_response.json()
    assert body["agent_id"] == agent["id"]
    assert body["version_restored"] == version_one["id"]

    history_response = client.get(f"/api/v1/agents/{agent['id']}/deployments")
    assert history_response.status_code == 200
    history = history_response.json()
    assert [entry["event_type"] for entry in history] == [
        "PROMOTE",
        "PROMOTE",
        "ROLLBACK",
    ]
