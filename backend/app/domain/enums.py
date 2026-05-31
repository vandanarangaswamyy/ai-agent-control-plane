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


class PolicyDecision(StrEnum):
    """Safety policy decisions for tool execution."""

    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"


class ApprovalStatus(StrEnum):
    """Lifecycle states for approval requests."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class EvaluationStatus(StrEnum):
    """Lifecycle states for evaluation executions."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"


class EvaluationResultStatus(StrEnum):
    """Outcome states for individual evaluation cases."""

    PASSED = "PASSED"
    FAILED = "FAILED"


class TraceEventType(StrEnum):
    """High-level trace event categories."""

    AGENT_RUN = "AGENT_RUN"
    TOOL_CALL = "TOOL_CALL"
    POLICY_CHECK = "POLICY_CHECK"
    EVALUATION = "EVALUATION"
    DEPLOYMENT = "DEPLOYMENT"


class DeploymentEventType(StrEnum):
    """Lifecycle events recorded by deployment control."""

    PROMOTE = "PROMOTE"
    ROLLBACK = "ROLLBACK"
    DEPRECATE = "DEPRECATE"
