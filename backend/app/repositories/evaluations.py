from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models.evaluation import Evaluation, EvaluationResult
from app.domain.enums import EvaluationResultStatus, EvaluationStatus


class EvaluationRepository:
    """Persistence operations for evaluations and case results."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_evaluation(
        self,
        *,
        agent_version_id: uuid.UUID,
        suite_name: str,
        trace_id: str,
    ) -> Evaluation:
        evaluation = Evaluation(
            agent_version_id=agent_version_id,
            suite_name=suite_name,
            trace_id=trace_id,
        )
        self._session.add(evaluation)
        self._session.flush()
        return evaluation

    def list_evaluations(self, *, limit: int, offset: int) -> list[Evaluation]:
        statement: Select[tuple[Evaluation]] = (
            select(Evaluation).order_by(Evaluation.created_at.desc()).limit(limit).offset(offset)
        )
        return list(self._session.scalars(statement).all())

    def get_evaluation(self, evaluation_id: uuid.UUID) -> Evaluation | None:
        return self._session.get(Evaluation, evaluation_id)

    def get_evaluation_for_update(self, evaluation_id: uuid.UUID) -> Evaluation | None:
        statement = select(Evaluation).where(Evaluation.id == evaluation_id).with_for_update()
        return self._session.scalars(statement).one_or_none()

    def get_latest_completed_evaluation_for_version_and_suite(
        self,
        *,
        agent_version_id: uuid.UUID,
        suite_name: str,
    ) -> Evaluation | None:
        statement = (
            select(Evaluation)
            .where(
                Evaluation.agent_version_id == agent_version_id,
                Evaluation.suite_name == suite_name,
                Evaluation.status.in_(
                    [EvaluationStatus.PASSED, EvaluationStatus.FAILED],
                ),
            )
            .order_by(Evaluation.created_at.desc(), Evaluation.id.desc())
            .limit(1)
        )
        return self._session.scalars(statement).one_or_none()

    def get_latest_completed_evaluation_for_version(
        self,
        agent_version_id: uuid.UUID,
    ) -> Evaluation | None:
        statement = (
            select(Evaluation)
            .where(
                Evaluation.agent_version_id == agent_version_id,
                Evaluation.status.in_(
                    [EvaluationStatus.PASSED, EvaluationStatus.FAILED],
                ),
            )
            .order_by(Evaluation.created_at.desc(), Evaluation.id.desc())
            .limit(1)
        )
        return self._session.scalars(statement).one_or_none()

    def create_result(
        self,
        *,
        evaluation_id: uuid.UUID,
        case_name: str,
        task: str,
        status: EvaluationResultStatus,
        run_id: uuid.UUID | None,
        tool_call_id: uuid.UUID | None,
        expected_tool_name: str | None,
        actual_tool_name: str | None,
        output: dict[str, object] | None,
        error_message: str | None,
        latency_ms: int | None,
        token_count: int | None,
        estimated_cost: Decimal | None,
        trace_id: str,
    ) -> EvaluationResult:
        result = EvaluationResult(
            evaluation_id=evaluation_id,
            case_name=case_name,
            task=task,
            status=status,
            run_id=run_id,
            tool_call_id=tool_call_id,
            expected_tool_name=expected_tool_name,
            actual_tool_name=actual_tool_name,
            output=output,
            error_message=error_message,
            latency_ms=latency_ms,
            token_count=token_count,
            estimated_cost=estimated_cost,
            trace_id=trace_id,
        )
        self._session.add(result)
        self._session.flush()
        return result

    def list_results_for_evaluation(self, evaluation_id: uuid.UUID) -> list[EvaluationResult]:
        statement: Select[tuple[EvaluationResult]] = (
            select(EvaluationResult)
            .where(EvaluationResult.evaluation_id == evaluation_id)
            .order_by(EvaluationResult.created_at.asc(), EvaluationResult.id.asc())
        )
        return list(self._session.scalars(statement).all())

    def flush(self) -> None:
        self._session.flush()
