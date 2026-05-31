from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_observability_service
from app.schemas.observability import TraceLookupRead
from app.services.observability import ObservabilityService

router = APIRouter(prefix="/traces", tags=["traces"])

ObservabilityDependency = Annotated[ObservabilityService, Depends(get_observability_service)]


@router.get("/{trace_id}", response_model=TraceLookupRead)
def get_trace(
    trace_id: str,
    service: ObservabilityDependency,
) -> TraceLookupRead:
    result = service.get_trace(trace_id)
    return TraceLookupRead(trace_id=result.trace_id, events=list(result.events))
