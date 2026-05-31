from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.domain.enums import ApprovalStatus, PolicyDecision

Reviewer = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class ApprovalReviewRequest(BaseModel):
    """Request body for approval review actions."""

    model_config = ConfigDict(extra="forbid")

    reviewed_by: Reviewer | None = None


class ApprovalRequestRead(BaseModel):
    """Approval request response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_run_id: uuid.UUID | None
    tool_call_id: uuid.UUID | None
    policy_decision: PolicyDecision
    reason: str
    requested_action: dict[str, Any]
    status: ApprovalStatus
    requested_by: str | None
    reviewed_by: str | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
