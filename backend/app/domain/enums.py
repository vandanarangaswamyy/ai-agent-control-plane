from __future__ import annotations

from enum import StrEnum


class HealthStatus(StrEnum):
    """Status values used by health endpoints."""

    OK = "ok"
    READY = "ready"
    NOT_READY = "not_ready"


class AgentVersionLifecycle(StrEnum):
    """Lifecycle states for versioned agent configurations."""

    DRAFT = "DRAFT"
    EVALUATED = "EVALUATED"
    APPROVED = "APPROVED"
    PRODUCTION = "PRODUCTION"
    DEPRECATED = "DEPRECATED"


class AgentRunStatus(StrEnum):
    """Execution lifecycle states for an agent run."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class ToolCallStatus(StrEnum):
    """Execution lifecycle states for a tool invocation."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class TraceEventType(StrEnum):
    """High-level trace event categories."""

    AGENT_RUN = "AGENT_RUN"
    TOOL_CALL = "TOOL_CALL"
