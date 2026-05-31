from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_evaluation_service
from app.repositories.approvals import ApprovalRepository
from app.repositories.evaluations import EvaluationRepository
from app.repositories.runtime import RuntimeRepository
from app.services.evaluation_suites import EvaluationSuiteLoader
from app.services.evaluations import EvaluationService
from app.services.policy import PolicyEngine
from app.services.runtime import RuntimeService
from app.services.safety_gateway import SafetyGateway
from app.tools.registry import ToolRegistry


def _create_agent(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "evaluation-api-agent",
            "description": "Evaluation test agent",
            "owner": "platform",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_agent_version(
    client: TestClient, *, agent_id: str, default_tool: str
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/agents/{agent_id}/versions",
        json={
            "name": f"{default_tool}-version",
            "prompt": "Use the configured runtime tool",
            "model": "claude-sonnet-4",
            "tool_config": {"default_tool": default_tool},
            "runtime_config": {"temperature": 0},
        },
    )
    assert response.status_code == 201
    return response.json()


def _override_get_evaluation_service(
    *,
    db_session_factory: sessionmaker[Session],
    suites_dir: Path,
):
    def override() -> EvaluationService:
        session = db_session_factory()
        runtime_repository = RuntimeRepository(session=session)
        safety_gateway = SafetyGateway(
            runtime_repository=runtime_repository,
            approval_repository=ApprovalRepository(session=session),
            tool_registry=ToolRegistry(),
            policy_engine=PolicyEngine(),
        )
        runtime_service = RuntimeService(
            session=session,
            repository=runtime_repository,
            safety_gateway=safety_gateway,
        )
        try:
            yield EvaluationService(
                session=session,
                evaluation_repository=EvaluationRepository(session=session),
                runtime_repository=runtime_repository,
                runtime_service=runtime_service,
                suite_loader=EvaluationSuiteLoader(suites_dir=suites_dir),
            )
        finally:
            session.close()

    return override


def test_evaluation_endpoints_support_execution_and_report(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
    tmp_path: Path,
) -> None:
    suite_path = tmp_path / "api-suite.json"
    suite_data = {
        "name": "api-suite",
        "cases": [
            {
                "name": "file-read-test",
                "task": "pyproject.toml",
                "tool_name": "file",
                "expected_tool_name": "file",
            },
            {
                "name": "browser-summary-test",
                "task": "search and summarize",
                "tool_name": "browser",
                "expected_tool_name": "browser",
            },
        ],
    }
    suite_path.write_text(
        json.dumps(suite_data, indent=2)
    )

    client.app.dependency_overrides[get_evaluation_service] = _override_get_evaluation_service(
        db_session_factory=db_session_factory,
        suites_dir=tmp_path,
    )

    try:
        agent = _create_agent(client)
        version = _create_agent_version(client, agent_id=str(agent["id"]), default_tool="browser")

        create_response = client.post(
            "/api/v1/evaluations",
            json={
                "agent_version_id": version["id"],
                "suite_name": "api-suite",
            },
        )
        assert create_response.status_code == 201
        evaluation = create_response.json()
        assert evaluation["status"] == "PASSED"
        assert evaluation["total_cases"] == 2

        list_response = client.get("/api/v1/evaluations")
        get_response = client.get(f"/api/v1/evaluations/{evaluation['id']}")
        report_response = client.get(f"/api/v1/evaluations/{evaluation['id']}/report")

        assert list_response.status_code == 200
        assert [item["id"] for item in list_response.json()] == [evaluation["id"]]
        assert get_response.status_code == 200
        assert get_response.json()["id"] == evaluation["id"]
        assert report_response.status_code == 200
        assert report_response.json()["suite"]["name"] == "api-suite"
        assert len(report_response.json()["results"]) == 2
    finally:
        client.app.dependency_overrides.pop(get_evaluation_service, None)


def test_compare_endpoint_detects_regressions(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
    tmp_path: Path,
) -> None:
    suite_path = tmp_path / "comparison-suite.json"
    suite_data = {
        "name": "comparison-suite",
        "cases": [
            {"name": "case-1", "task": "pyproject.toml"},
            {"name": "case-2", "task": "summarize text"},
        ],
    }
    suite_path.write_text(
        json.dumps(suite_data, indent=2)
    )

    client.app.dependency_overrides[get_evaluation_service] = _override_get_evaluation_service(
        db_session_factory=db_session_factory,
        suites_dir=tmp_path,
    )

    try:
        agent = _create_agent(client)
        base_version = _create_agent_version(
            client, agent_id=str(agent["id"]), default_tool="browser"
        )
        candidate_version = _create_agent_version(
            client,
            agent_id=str(agent["id"]),
            default_tool="terminal",
        )

        base_eval = client.post(
            "/api/v1/evaluations",
            json={
                "agent_version_id": base_version["id"],
                "suite_name": "comparison-suite",
            },
        )
        candidate_eval = client.post(
            "/api/v1/evaluations",
            json={
                "agent_version_id": candidate_version["id"],
                "suite_name": "comparison-suite",
            },
        )
        assert base_eval.status_code == 201
        assert candidate_eval.status_code == 201

        response = client.post(
            "/api/v1/evaluations/compare",
            json={
                "base_agent_version_id": base_version["id"],
                "candidate_agent_version_id": candidate_version["id"],
                "suite_name": "comparison-suite",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["regressions"]
        assert any(item["metric"] == "success_rate" for item in body["regressions"])
        assert any(item["metric"] == "failure_rate" for item in body["regressions"])
    finally:
        client.app.dependency_overrides.pop(get_evaluation_service, None)
