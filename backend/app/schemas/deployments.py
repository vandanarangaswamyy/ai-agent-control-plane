from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import DeploymentEventType


class DeploymentPromoteRequest(BaseModel):
    """Request body for promoting an agent version."""

    model_config = ConfigDict(extra="forbid")

    agent_id: uuid.UUID
    agent_version_id: uuid.UUID
    reason: str | None = Field(default=None, max_length=1000)


class DeploymentRollbackRequest(BaseModel):
    """Request body for rolling back an agent."""

    model_config = ConfigDict(extra="forbid")

    agent_id: uuid.UUID
    reason: str | None = Field(default=None, max_length=1000)


class DeploymentEventRead(BaseModel):
    """Deployment history response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    event_type: DeploymentEventType
    source_version_id: uuid.UUID | None
    target_version_id: uuid.UUID | None
    reason: str | None
    trace_id: str | None
    created_at: datetime
    updated_at: datetime


class DeploymentPromotionRead(BaseModel):
    """Promotion response."""

    agent_id: uuid.UUID
    version_promoted: uuid.UUID
    previous_production_version: uuid.UUID | None
    deployment_timestamp: datetime


class DeploymentRollbackRead(BaseModel):
    """Rollback response."""

    agent_id: uuid.UUID
    version_restored: uuid.UUID
    rollback_timestamp: datetime
