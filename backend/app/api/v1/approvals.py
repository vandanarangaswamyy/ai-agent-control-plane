from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_approval_service
from app.schemas.approvals import ApprovalRequestRead, ApprovalReviewRequest
from app.services.approvals import ApprovalService

router = APIRouter(prefix="/approvals", tags=["approvals"])

LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]
ApprovalDependency = Annotated[ApprovalService, Depends(get_approval_service)]


@router.get("", response_model=list[ApprovalRequestRead])
def list_approval_requests(
    service: ApprovalDependency,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[ApprovalRequestRead]:
    approvals = service.list_approval_requests(limit=limit, offset=offset)
    return [ApprovalRequestRead.model_validate(approval) for approval in approvals]


@router.get("/{approval_id}", response_model=ApprovalRequestRead)
def get_approval_request(
    approval_id: uuid.UUID,
    service: ApprovalDependency,
) -> ApprovalRequestRead:
    approval = service.get_approval_request(approval_id)
    return ApprovalRequestRead.model_validate(approval)


@router.post("/{approval_id}/approve", response_model=ApprovalRequestRead)
def approve_request(
    approval_id: uuid.UUID,
    payload: ApprovalReviewRequest,
    service: ApprovalDependency,
) -> ApprovalRequestRead:
    approval = service.approve(approval_id=approval_id, reviewed_by=payload.reviewed_by)
    return ApprovalRequestRead.model_validate(approval)


@router.post("/{approval_id}/reject", response_model=ApprovalRequestRead)
def reject_request(
    approval_id: uuid.UUID,
    payload: ApprovalReviewRequest,
    service: ApprovalDependency,
) -> ApprovalRequestRead:
    approval = service.reject(approval_id=approval_id, reviewed_by=payload.reviewed_by)
    return ApprovalRequestRead.model_validate(approval)
