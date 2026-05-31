from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_deployment_service
from app.schemas.deployments import (
    DeploymentPromoteRequest,
    DeploymentPromotionRead,
    DeploymentRollbackRead,
    DeploymentRollbackRequest,
)
from app.services.deployments import DeploymentService

router = APIRouter(prefix="/deployments", tags=["deployments"])

DeploymentDependency = Annotated[DeploymentService, Depends(get_deployment_service)]


@router.post(
    "/promote", response_model=DeploymentPromotionRead, status_code=status.HTTP_201_CREATED
)
def promote_deployment(
    payload: DeploymentPromoteRequest,
    service: DeploymentDependency,
) -> DeploymentPromotionRead:
    return service.promote_version(
        agent_id=payload.agent_id,
        agent_version_id=payload.agent_version_id,
        reason=payload.reason,
    )


@router.post("/rollback", response_model=DeploymentRollbackRead)
def rollback_deployment(
    payload: DeploymentRollbackRequest,
    service: DeploymentDependency,
) -> DeploymentRollbackRead:
    return service.rollback(
        agent_id=payload.agent_id,
        reason=payload.reason,
    )
