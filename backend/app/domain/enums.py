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
