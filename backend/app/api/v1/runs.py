from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_observability_service, get_runtime_service
from app.schemas.observability import RunFailureInspectionRead, RunTimelineRead
from app.schemas.runs import RunCreate, RunRead
from app.services.observability import ObservabilityService
from app.services.runtime import RuntimeService
from app.workers.tasks import execute_agent_run

router = APIRouter(prefix="/runs", tags=["runs"])

LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]
RuntimeDependency = Annotated[RuntimeService, Depends(get_runtime_service)]
ObservabilityDependency = Annotated[ObservabilityService, Depends(get_observability_service)]


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run(
    payload: RunCreate,
    service: RuntimeDependency,
) -> RunRead:
    if payload.execute_async:
        run = service.create_run(
            agent_version_id=payload.agent_version_id,
            task=payload.task,
            tool_name=payload.tool_name,
            tool_input=payload.tool_input,
        )
        execute_agent_run.delay(str(run.id))
        return RunRead.model_validate(run)

    run = service.create_and_execute_run(
        agent_version_id=payload.agent_version_id,
        task=payload.task,
        tool_name=payload.tool_name,
        tool_input=payload.tool_input,
    )
    return RunRead.model_validate(run)


@router.get("", response_model=list[RunRead])
def list_runs(
    service: RuntimeDependency,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[RunRead]:
    runs = service.list_runs(limit=limit, offset=offset)
    return [RunRead.model_validate(run) for run in runs]


@router.get("/{run_id}", response_model=RunRead)
def get_run(
    run_id: uuid.UUID,
    service: RuntimeDependency,
) -> RunRead:
    run = service.get_run(run_id)
    return RunRead.model_validate(run)


@router.get("/{run_id}/timeline", response_model=RunTimelineRead)
def get_run_timeline(
    run_id: uuid.UUID,
    service: ObservabilityDependency,
) -> RunTimelineRead:
    result = service.get_run_timeline(run_id)
    return RunTimelineRead(
        run=RunRead.model_validate(result.run),
        events=list(result.events),
    )


@router.get("/{run_id}/failures", response_model=RunFailureInspectionRead)
def get_run_failures(
    run_id: uuid.UUID,
    service: ObservabilityDependency,
) -> RunFailureInspectionRead:
    result = service.get_run_failures(run_id)
    return RunFailureInspectionRead(
        run=RunRead.model_validate(result.run),
        runtime_error_message=result.runtime_error_message,
        failed_tool_calls=list(result.failed_tool_calls),
        blocked_tool_calls=list(result.blocked_tool_calls),
        denied_policy_checks=list(result.denied_policy_checks),
        approval_failures=list(result.approval_failures),
        trace_events=list(result.trace_events),
    )
