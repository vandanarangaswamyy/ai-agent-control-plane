from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_app_settings, get_health_service
from app.core.config import Settings
from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.health import HealthService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Annotated[Settings, Depends(get_app_settings)]) -> HealthResponse:
    """Return process-level health without touching dependencies."""
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )


@router.get("/ready", response_model=ReadinessResponse)
def readiness(
    response: Response,
    health_service: Annotated[HealthService, Depends(get_health_service)],
) -> ReadinessResponse:
    """Return dependency readiness for load balancers and local smoke tests."""
    result = health_service.readiness()
    if result.status != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result

