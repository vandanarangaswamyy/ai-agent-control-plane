from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.domain.enums import TraceEventType
from app.schemas.approvals import ApprovalRequestRead
from app.schemas.runs import RunRead, ToolCallRead


class TraceEventRead(BaseModel):
    """Persisted trace event response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trace_id: str
    span_id: str | None
    parent_span_id: str | None
    event_type: TraceEventType
    entity_type: str
    entity_id: uuid.UUID | None
    name: str
    attributes: dict[str, Any]
    timestamp: datetime


class TraceLookupRead(BaseModel):
    """Trace lookup response grouped by trace identifier."""

    trace_id: str
    events: list[TraceEventRead]


class RunTimelineRead(BaseModel):
    """Chronological run timeline response."""

    run: RunRead
    events: list[TraceEventRead]


class RunFailureInspectionRead(BaseModel):
    """Structured failure analysis for a run."""

    run: RunRead
    runtime_error_message: str | None
    failed_tool_calls: list[ToolCallRead]
    blocked_tool_calls: list[ToolCallRead]
    denied_policy_checks: list[TraceEventRead]
    approval_failures: list[ApprovalRequestRead]
    trace_events: list[TraceEventRead]
