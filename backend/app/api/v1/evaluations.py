from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_evaluation_service
from app.schemas.evaluations import (
    EvaluationCompareRequest,
    EvaluationComparisonRead,
    EvaluationCreateRequest,
    EvaluationRead,
    EvaluationReportRead,
)
from app.services.evaluations import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]
EvaluationDependency = Annotated[EvaluationService, Depends(get_evaluation_service)]


@router.post("", response_model=EvaluationRead, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    payload: EvaluationCreateRequest,
    service: EvaluationDependency,
) -> EvaluationRead:
    evaluation = service.run_evaluation(
        agent_version_id=payload.agent_version_id,
        suite_name=payload.suite_name,
    )
    return EvaluationRead.model_validate(evaluation)


@router.get("", response_model=list[EvaluationRead])
def list_evaluations(
    service: EvaluationDependency,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[EvaluationRead]:
    evaluations = service.list_evaluations(limit=limit, offset=offset)
    return [EvaluationRead.model_validate(evaluation) for evaluation in evaluations]


@router.post("/compare", response_model=EvaluationComparisonRead)
def compare_evaluations(
    payload: EvaluationCompareRequest,
    service: EvaluationDependency,
) -> EvaluationComparisonRead:
    return service.compare_versions(
        base_agent_version_id=payload.base_agent_version_id,
        candidate_agent_version_id=payload.candidate_agent_version_id,
        suite_name=payload.suite_name,
    )


@router.get("/{evaluation_id}", response_model=EvaluationRead)
def get_evaluation(
    evaluation_id: uuid.UUID,
    service: EvaluationDependency,
) -> EvaluationRead:
    evaluation = service.get_evaluation(evaluation_id)
    return EvaluationRead.model_validate(evaluation)


@router.get("/{evaluation_id}/report", response_model=EvaluationReportRead)
def get_evaluation_report(
    evaluation_id: uuid.UUID,
    service: EvaluationDependency,
) -> EvaluationReportRead:
    return service.get_report(evaluation_id)
