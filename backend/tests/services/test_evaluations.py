from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.evaluation import Evaluation
from app.db.models.runtime import Trace
from app.domain.enums import EvaluationResultStatus, EvaluationStatus
from app.domain.errors import BusinessRuleViolationError
from app.repositories.agents import AgentRepository
from app.repositories.approvals import ApprovalRepository
from app.repositories.evaluations import EvaluationRepository
from app.repositories.runtime import RuntimeRepository
from app.services.agent_registry import AgentRegistryService
from app.services.evaluation_suites import EvaluationSuiteLoader
from app.services.evaluations import EvaluationService
from app.services.policy import PolicyEngine
from app.services.runtime import RuntimeService
from app.services.safety_gateway import SafetyGateway
from app.tools.registry import ToolRegistry


def _create_agent_version(session: Session, *, default_tool: str = "browser"):
    agent_service = AgentRegistryService(
        session=session,
        repository=AgentRepository(session=session),
    )
    agent = agent_service.create_agent(
        name=f"evaluation-agent-{default_tool}",
        description=None,
        owner=None,
    )
    return agent_service.create_version(
        agent_id=agent.id,
        name="evaluation",
        prompt="Use evaluation",
        model="claude-sonnet-4",
        tool_config={"default_tool": default_tool},
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


def _build_evaluation_service(
    session: Session,
    *,
    suites_dir: Path | None = None,
) -> EvaluationService:
    runtime_service = _build_runtime_service(session)
    return EvaluationService(
        session=session,
        evaluation_repository=EvaluationRepository(session=session),
        runtime_repository=runtime_service.repository,
        runtime_service=runtime_service,
        suite_loader=EvaluationSuiteLoader(suites_dir=suites_dir),
    )


def test_suite_loader_validates_schema(tmp_path: Path) -> None:
    suite_file = tmp_path / "valid-suite.json"
    suite_file.write_text(
        """
        {
          "name": "valid-suite",
          "cases": [
            {"name": "case-1", "task": "read file"}
          ]
        }
        """
    )
    loader = EvaluationSuiteLoader(suites_dir=tmp_path)
    suite = loader.load_suite("valid-suite")

    assert suite.name == "valid-suite"
    assert suite.cases[0].name == "case-1"

    invalid_file = tmp_path / "invalid-suite.json"
    invalid_file.write_text(
        """
        {
          "name": "invalid-suite",
          "cases": [
            {"name": "dup", "task": "one"},
            {"name": "dup", "task": "two"}
          ]
        }
        """
    )
    with pytest.raises(BusinessRuleViolationError):
        loader.load_suite("invalid-suite")


def test_evaluation_execution_persists_results_and_report(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        version = _create_agent_version(session)
        service = _build_evaluation_service(session)

        evaluation = service.run_evaluation(
            agent_version_id=version.id,
            suite_name="basic-agent-suite",
        )

        assert evaluation.status == EvaluationStatus.PASSED
        assert evaluation.total_cases == 2
        assert evaluation.passed_cases == 2
        assert evaluation.failed_cases == 0
        assert evaluation.success_rate == Decimal("1.000000")
        assert evaluation.tool_accuracy == Decimal("1.000000")
        assert evaluation.average_latency_ms is not None
        assert evaluation.total_cost is not None
        assert evaluation.failure_rate == Decimal("0.000000")
        assert evaluation.report is not None
        assert evaluation.report["suite"]["name"] == "basic-agent-suite"

        persisted_evaluation = session.get(Evaluation, evaluation.id)
        assert persisted_evaluation is not None
        assert len(persisted_evaluation.results) == 2
        assert all(
            result.status == EvaluationResultStatus.PASSED
            for result in persisted_evaluation.results
        )
        assert all(result.run_id is not None for result in persisted_evaluation.results)

        trace_names = {trace.name for trace in session.scalars(select(Trace)).all()}
        assert {"EvaluationStarted", "CaseExecuted", "EvaluationCompleted"} <= trace_names


def test_compare_versions_detects_regressions(
    db_session_factory: sessionmaker[Session],
    tmp_path: Path,
) -> None:
    suite_file = tmp_path / "regression-suite.json"
    suite_file.write_text(
        """
        {
          "name": "regression-suite",
          "cases": [
            {"name": "case-1", "task": "pyproject.toml"},
            {"name": "case-2", "task": "summarize text"}
          ]
        }
        """
    )

    with db_session_factory() as session:
        base_version = _create_agent_version(session, default_tool="browser")
        candidate_version = _create_agent_version(session, default_tool="terminal")
        service = _build_evaluation_service(session, suites_dir=tmp_path)

        service.run_evaluation(
            agent_version_id=base_version.id,
            suite_name="regression-suite",
        )
        service.run_evaluation(
            agent_version_id=candidate_version.id,
            suite_name="regression-suite",
        )

        comparison = service.compare_versions(
            base_agent_version_id=base_version.id,
            candidate_agent_version_id=candidate_version.id,
            suite_name="regression-suite",
        )

        regression_metrics = {finding.metric for finding in comparison.regressions}
        assert "success_rate" in regression_metrics
        assert "failure_rate" in regression_metrics
        assert "tool_accuracy" in regression_metrics
        assert comparison.candidate_evaluation.status == EvaluationStatus.FAILED
