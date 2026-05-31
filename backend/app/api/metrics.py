from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_metrics_service
from app.core.metrics import ObservabilityMetrics

router = APIRouter(tags=["metrics"])

MetricsDependency = Annotated[ObservabilityMetrics, Depends(get_metrics_service)]


@router.get("/metrics")
def get_metrics(service: MetricsDependency) -> Response:
    return Response(content=service.render(), media_type=service.content_type)
