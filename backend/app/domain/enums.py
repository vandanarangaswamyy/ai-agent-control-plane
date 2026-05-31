from __future__ import annotations

from enum import StrEnum


class HealthStatus(StrEnum):
    """Status values used by health endpoints."""

    OK = "ok"
    READY = "ready"
    NOT_READY = "not_ready"

