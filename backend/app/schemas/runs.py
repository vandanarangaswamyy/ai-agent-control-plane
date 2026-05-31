from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.domain.enums import AgentRunStatus, ToolCallStatus

TaskText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ToolName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class RunCreate(BaseModel):
    """Request body for creating an agent run."""

    model_config = ConfigDict(extra="forbid")

    agent_version_id: uuid.UUID
    task: TaskText
    execute_async: bool = False
    tool_name: ToolName | None = None
    tool_input: dict[str, Any] | None = None


class RunRead(BaseModel):
    """Agent run response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    agent_version_id: uuid.UUID
    status: AgentRunStatus
    input: dict[str, Any]
    output: dict[str, Any] | None
    error_message: str | None
    start_time: datetime | None
    end_time: datetime | None
    latency_ms: int | None
    token_count: int | None
    estimated_cost: Decimal | None = Field(default=None)
    trace_id: str | None
    created_at: datetime
    updated_at: datetime


class ToolCallRead(BaseModel):
    """Tool invocation response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_run_id: uuid.UUID
    tool_name: str
    status: ToolCallStatus
    input: dict[str, Any]
    output: dict[str, Any] | None
    error_message: str | None
    start_time: datetime | None
    end_time: datetime | None
    latency_ms: int | None
    trace_id: str | None
    span_id: str | None
    created_at: datetime
    updated_at: datetime
