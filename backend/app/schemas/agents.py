from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.domain.enums import AgentVersionLifecycle

AgentName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
OptionalName = Annotated[
    str | None,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
PromptText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ModelName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class AgentCreate(BaseModel):
    """Request body for creating an agent."""

    model_config = ConfigDict(extra="forbid")

    name: AgentName
    description: str | None = None
    owner: OptionalName = None


class AgentRead(BaseModel):
    """Agent response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    owner: str | None
    created_at: datetime
    updated_at: datetime


class AgentVersionCreate(BaseModel):
    """Request body for creating an agent version."""

    model_config = ConfigDict(extra="forbid")

    name: OptionalName = None
    prompt: PromptText
    model: ModelName
    tool_config: dict[str, Any] = Field(default_factory=dict)
    runtime_config: dict[str, Any] = Field(default_factory=dict)


class AgentVersionUpdate(BaseModel):
    """Request body for updating editable draft version metadata."""

    model_config = ConfigDict(extra="forbid")

    name: OptionalName = None
    prompt: PromptText | None = None
    model: ModelName | None = None
    tool_config: dict[str, Any] | None = None
    runtime_config: dict[str, Any] | None = None

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> AgentVersionUpdate:
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        return self


class AgentVersionRead(BaseModel):
    """Agent version response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    version: int
    name: str | None
    prompt: str
    model: str
    tool_config: dict[str, Any]
    runtime_config: dict[str, Any]
    lifecycle: AgentVersionLifecycle
    created_at: datetime
    updated_at: datetime
