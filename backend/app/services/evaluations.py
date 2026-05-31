from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.telemetry import get_tracer
from app.db.models.evaluation import Evaluation, EvaluationResult
from app.domain.enums import (
    AgentRunStatus,
    EvaluationResultStatus,
    EvaluationStatus,
    TraceEventType,
)
from app.domain.errors import NotFoundError
from app.repositories.evaluations import EvaluationRepository
from app.repositories.runtime import RuntimeRepository
from app.schemas.evaluations import (
    EvaluationComparisonRead,
    EvaluationFindingRead,
    EvaluationMetricDeltaRead,
    EvaluationReportRead,
    EvaluationSuiteDefinition,
)
from app.services.evaluation_suites import EvaluationSuiteLoader
from app.services.runtime import RuntimeService


class EvaluationService:
    """Business workflows for running and comparing evaluation suites."""

    def __init__(
        self,
        *,
        session: Session,
        evaluation_repository: EvaluationRepository,
        runtime_repository: RuntimeRepository,
        runtime_service: RuntimeService,
        suite_loader: EvaluationSuiteLoader | None = None,
    ) -> None:
        self._session = session
        self._evaluation_repository = evaluation_repository
        self._runtime_repository = runtime_repository
        self._runtime_service = runtime_service
        self._suite_loader = suite_loader or EvaluationSuiteLoader()

    def list_evaluations(self, *, limit: int, offset: int) -> list[Evaluation]:
        return self._evaluation_repository.list_evaluations(limit=limit, offset=offset)

    def get_evaluation(self, evaluation_id: uuid.UUID) -> Evaluation:
        evaluation = self._evaluation_repository.get_evaluation(evaluation_id)
        if evaluation is None:
            raise NotFoundError("evaluation not found")
        return evaluation

    def run_evaluation(self, *, agent_version_id: uuid.UUID, suite_name: str) -> Evaluation:
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("evaluation.execute") as span:
            span.set_attribute("agent_version_id", str(agent_version_id))
            span.set_attribute("suite_name", suite_name)
            suite = self._suite_loader.load_suite(suite_name)
            trace_id = uuid.uuid4().hex

            evaluation = self._evaluation_repository.create_evaluation(
                agent_version_id=agent_version_id,
                suite_name=suite.name,
                trace_id=trace_id,
            )
            self._session.commit()

            evaluation.status = EvaluationStatus.RUNNING
            evaluation.started_at = _utc_now()
            self._trace_evaluation(
                evaluation=evaluation,
                event_name="EvaluationStarted",
                attributes={
                    "suite_name": suite.name,
                    "case_count": len(suite.cases),
                    "agent_version_id": str(agent_version_id),
                },
            )
            self._session.commit()

            results: list[EvaluationResult] = []
            try:
                for case in suite.cases:
                    result = self._execute_case(
                        evaluation=evaluation,
                        case_name=case.name,
                        task=case.task,
                        tool_name=case.tool_name,
                        expected_tool_name=case.expected_tool_name,
                    )
                    results.append(result)
                    self._session.commit()

                self._finalize_evaluation(
                    evaluation=evaluation,
                    suite=suite,
                    results=results,
                )
                self._session.commit()
                self._session.refresh(evaluation)
                span.set_attribute("evaluation.status", evaluation.status.value)
                return evaluation
            except Exception as exc:
                self._session.rollback()
                failed = self._finalize_failed_evaluation(
                    evaluation_id=evaluation.id,
                    suite=suite,
                    error_message=str(exc),
                )
                span.record_exception(exc)
                span.set_attribute("evaluation.status", failed.status.value)
                return failed

    def get_report(self, evaluation_id: uuid.UUID) -> EvaluationReportRead:
        evaluation = self.get_evaluation(evaluation_id)
        results = self._evaluation_repository.list_results_for_evaluation(evaluation.id)
        report = evaluation.report or self._build_report(
            evaluation=evaluation,
            suite=self._suite_loader.load_suite(evaluation.suite_name),
            results=results,
        )
        suite = EvaluationSuiteDefinition.model_validate(report["suite"])
        return EvaluationReportRead(
            evaluation=evaluation,
            suite=suite,
            results=results,
            report=report,
        )

    def compare_versions(
        self,
        *,
        base_agent_version_id: uuid.UUID,
        candidate_agent_version_id: uuid.UUID,
        suite_name: str,
    ) -> EvaluationComparisonRead:
        base = self._evaluation_repository.get_latest_completed_evaluation_for_version_and_suite(
            agent_version_id=base_agent_version_id,
            suite_name=suite_name,
        )
        candidate = (
            self._evaluation_repository.get_latest_completed_evaluation_for_version_and_suite(
                agent_version_id=candidate_agent_version_id,
                suite_name=suite_name,
            )
        )
        if base is None or candidate is None:
            raise NotFoundError("completed evaluations not found for comparison")

        base_report = self.get_report(base.id)
        candidate_report = self.get_report(candidate.id)
        metric_deltas = self._metric_deltas(base, candidate)
        regressions, improvements = self._compare_findings(base, candidate)
        return EvaluationComparisonRead(
            base_evaluation=base_report.evaluation,
            candidate_evaluation=candidate_report.evaluation,
            metric_deltas=metric_deltas,
            regressions=regressions,
            improvements=improvements,
        )

    def _execute_case(
        self,
        *,
        evaluation: Evaluation,
        case_name: str,
        task: str,
        tool_name: str | None,
        expected_tool_name: str | None,
    ) -> EvaluationResult:
        run = self._runtime_service.create_and_execute_run(
            agent_version_id=evaluation.agent_version_id,
            task=task,
            tool_name=tool_name,
        )
        tool_calls = self._runtime_repository.list_tool_calls_for_run(run.id)
        tool_call = tool_calls[0] if tool_calls else None
        actual_tool_name = (
            tool_call.tool_name if tool_call is not None else self._extract_tool_name(run)
        )
        passed = run.status == AgentRunStatus.SUCCESS and (
            expected_tool_name is None or actual_tool_name == expected_tool_name
        )
        status = EvaluationResultStatus.PASSED if passed else EvaluationResultStatus.FAILED
        result = self._evaluation_repository.create_result(
            evaluation_id=evaluation.id,
            case_name=case_name,
            task=task,
            status=status,
            run_id=run.id,
            tool_call_id=tool_call.id if tool_call is not None else None,
            expected_tool_name=expected_tool_name,
            actual_tool_name=actual_tool_name,
            output=run.output,
            error_message=run.error_message,
            latency_ms=run.latency_ms,
            token_count=run.token_count,
            estimated_cost=run.estimated_cost or Decimal("0.000000"),
            trace_id=evaluation.trace_id or uuid.uuid4().hex,
        )
        self._trace_evaluation(
            evaluation=evaluation,
            event_name="CaseExecuted",
            attributes={
                "case_name": case_name,
                "status": status.value,
                "run_id": str(run.id),
                "tool_call_id": str(tool_call.id) if tool_call is not None else None,
                "actual_tool_name": actual_tool_name,
                "expected_tool_name": expected_tool_name,
                "latency_ms": run.latency_ms,
                "estimated_cost": str(run.estimated_cost or Decimal("0.000000")),
                "error_message": run.error_message,
            },
        )
        return result

    def _finalize_evaluation(
        self,
        *,
        evaluation: Evaluation,
        suite: EvaluationSuiteDefinition,
        results: list[EvaluationResult],
    ) -> None:
        metrics = self._compute_metrics(results)
        evaluation.status = (
            EvaluationStatus.PASSED if metrics["failed_cases"] == 0 else EvaluationStatus.FAILED
        )
        evaluation.finished_at = _utc_now()
        evaluation.total_cases = metrics["total_cases"]
        evaluation.passed_cases = metrics["passed_cases"]
        evaluation.failed_cases = metrics["failed_cases"]
        evaluation.success_rate = metrics["success_rate"]
        evaluation.tool_accuracy = metrics["tool_accuracy"]
        evaluation.average_latency_ms = metrics["average_latency_ms"]
        evaluation.total_cost = metrics["total_cost"]
        evaluation.failure_rate = metrics["failure_rate"]
        evaluation.report = self._build_report(
            evaluation=evaluation,
            suite=suite,
            results=results,
        )
        self._trace_evaluation(
            evaluation=evaluation,
            event_name="EvaluationCompleted",
            attributes={
                "status": evaluation.status.value,
                "success_rate": str(evaluation.success_rate),
                "failure_rate": str(evaluation.failure_rate),
            },
        )

    def _finalize_failed_evaluation(
        self,
        *,
        evaluation_id: uuid.UUID,
        suite: EvaluationSuiteDefinition,
        error_message: str,
    ) -> Evaluation:
        evaluation = self._evaluation_repository.get_evaluation_for_update(evaluation_id)
        if evaluation is None:
            raise NotFoundError("evaluation not found")

        results = self._evaluation_repository.list_results_for_evaluation(evaluation.id)
        metrics = self._compute_metrics(results)
        evaluation.status = EvaluationStatus.FAILED
        evaluation.error_message = error_message
        evaluation.finished_at = _utc_now()
        evaluation.total_cases = metrics["total_cases"]
        evaluation.passed_cases = metrics["passed_cases"]
        evaluation.failed_cases = metrics["failed_cases"]
        evaluation.success_rate = metrics["success_rate"]
        evaluation.tool_accuracy = metrics["tool_accuracy"]
        evaluation.average_latency_ms = metrics["average_latency_ms"]
        evaluation.total_cost = metrics["total_cost"]
        evaluation.failure_rate = metrics["failure_rate"]
        evaluation.report = self._build_report(
            evaluation=evaluation,
            suite=suite,
            results=results,
        )
        self._trace_evaluation(
            evaluation=evaluation,
            event_name="EvaluationFailed",
            attributes={
                "error_message": error_message,
                "status": evaluation.status.value,
            },
        )
        self._session.commit()
        self._session.refresh(evaluation)
        return evaluation

    def _compute_metrics(self, results: list[EvaluationResult]) -> dict[str, Decimal | int]:
        total_cases = len(results)
        passed_cases = sum(
            1 for result in results if result.status == EvaluationResultStatus.PASSED
        )
        failed_cases = total_cases - passed_cases
        success_rate = self._ratio(passed_cases, total_cases)
        failure_rate = self._ratio(failed_cases, total_cases)

        actual_tool_successes = sum(
            1
            for result in results
            if result.status == EvaluationResultStatus.PASSED
            and (
                result.expected_tool_name is None
                or result.actual_tool_name == result.expected_tool_name
            )
        )
        tool_accuracy = self._ratio(actual_tool_successes, total_cases)

        latencies = [result.latency_ms for result in results if result.latency_ms is not None]
        average_latency_ms = int(sum(latencies) / len(latencies)) if latencies else 0
        total_cost = Decimal("0.000000")
        for result in results:
            total_cost += result.estimated_cost or Decimal("0.000000")
        return {
            "total_cases": total_cases,
            "passed_cases": passed_cases,
            "failed_cases": failed_cases,
            "success_rate": success_rate,
            "tool_accuracy": tool_accuracy,
            "average_latency_ms": average_latency_ms,
            "total_cost": total_cost,
            "failure_rate": failure_rate,
        }

    def _build_report(
        self,
        *,
        evaluation: Evaluation,
        suite: EvaluationSuiteDefinition,
        results: list[EvaluationResult],
    ) -> dict[str, object]:
        metrics = self._compute_metrics(results)
        return {
            "evaluation_id": str(evaluation.id),
            "agent_version_id": str(evaluation.agent_version_id),
            "suite": suite.model_dump(),
            "status": evaluation.status.value,
            "metrics": {
                "success_rate": str(metrics["success_rate"]),
                "tool_accuracy": str(metrics["tool_accuracy"]),
                "latency_ms": metrics["average_latency_ms"],
                "cost": str(metrics["total_cost"]),
                "failure_rate": str(metrics["failure_rate"]),
            },
            "results": [
                {
                    "case_name": result.case_name,
                    "status": result.status.value,
                    "run_id": str(result.run_id) if result.run_id is not None else None,
                    "tool_call_id": str(result.tool_call_id)
                    if result.tool_call_id is not None
                    else None,
                    "actual_tool_name": result.actual_tool_name,
                    "expected_tool_name": result.expected_tool_name,
                    "latency_ms": result.latency_ms,
                    "error_message": result.error_message,
                    "estimated_cost": str(result.estimated_cost or Decimal("0.000000")),
                }
                for result in results
            ],
        }

    def _metric_deltas(
        self,
        base: Evaluation,
        candidate: Evaluation,
    ) -> list[EvaluationMetricDeltaRead]:
        metric_pairs = [
            ("success_rate", base.success_rate, candidate.success_rate),
            ("tool_accuracy", base.tool_accuracy, candidate.tool_accuracy),
            ("latency_ms", base.average_latency_ms, candidate.average_latency_ms),
            ("cost", base.total_cost, candidate.total_cost),
            ("failure_rate", base.failure_rate, candidate.failure_rate),
        ]
        deltas: list[EvaluationMetricDeltaRead] = []
        for metric, base_value, candidate_value in metric_pairs:
            delta = self._subtract(candidate_value, base_value)
            deltas.append(
                EvaluationMetricDeltaRead(
                    metric=metric,
                    base_value=base_value,
                    candidate_value=candidate_value,
                    delta=delta,
                )
            )
        return deltas

    def _compare_findings(
        self,
        base: Evaluation,
        candidate: Evaluation,
    ) -> tuple[list[EvaluationFindingRead], list[EvaluationFindingRead]]:
        regressions: list[EvaluationFindingRead] = []
        improvements: list[EvaluationFindingRead] = []

        for metric, base_value, candidate_value in (
            ("success_rate", base.success_rate, candidate.success_rate),
            ("tool_accuracy", base.tool_accuracy, candidate.tool_accuracy),
            ("latency_ms", base.average_latency_ms, candidate.average_latency_ms),
            ("cost", base.total_cost, candidate.total_cost),
            ("failure_rate", base.failure_rate, candidate.failure_rate),
        ):
            delta = self._subtract(candidate_value, base_value)
            if delta is None:
                continue
            if metric in {"success_rate", "tool_accuracy"}:
                if delta < 0:
                    regressions.append(
                        EvaluationFindingRead(
                            metric=metric,
                            base_value=base_value,
                            candidate_value=candidate_value,
                            delta=delta,
                            reason=f"{metric} decreased",
                        )
                    )
                elif delta > 0:
                    improvements.append(
                        EvaluationFindingRead(
                            metric=metric,
                            base_value=base_value,
                            candidate_value=candidate_value,
                            delta=delta,
                            reason=f"{metric} increased",
                        )
                    )
            elif metric in {"latency_ms", "cost", "failure_rate"}:
                if delta > 0:
                    regressions.append(
                        EvaluationFindingRead(
                            metric=metric,
                            base_value=base_value,
                            candidate_value=candidate_value,
                            delta=delta,
                            reason=f"{metric} increased",
                        )
                    )
                elif delta < 0:
                    improvements.append(
                        EvaluationFindingRead(
                            metric=metric,
                            base_value=base_value,
                            candidate_value=candidate_value,
                            delta=delta,
                            reason=f"{metric} decreased",
                        )
                    )

        return regressions, improvements

    def _trace_evaluation(
        self,
        *,
        evaluation: Evaluation,
        event_name: str,
        attributes: dict[str, object],
    ) -> None:
        self._runtime_repository.create_trace(
            trace_id=evaluation.trace_id or uuid.uuid4().hex,
            event_type=TraceEventType.EVALUATION,
            entity_type="evaluation",
            entity_id=evaluation.id,
            name=event_name,
            attributes=attributes,
        )

    def _extract_tool_name(self, run: object) -> str | None:
        output = getattr(run, "output", None)
        if isinstance(output, dict):
            tool = output.get("tool")
            if tool is not None:
                return str(tool)
        return None

    def _ratio(self, numerator: int, denominator: int) -> Decimal:
        if denominator == 0:
            return Decimal("0.000000")
        return (Decimal(numerator) / Decimal(denominator)).quantize(Decimal("0.000001"))

    def _subtract(
        self, left: Decimal | int | None, right: Decimal | int | None
    ) -> Decimal | int | None:
        if left is None or right is None:
            return None
        if isinstance(left, Decimal) or isinstance(right, Decimal):
            return Decimal(left) - Decimal(right)
        return left - right


def _utc_now() -> datetime:
    return datetime.now(UTC)
