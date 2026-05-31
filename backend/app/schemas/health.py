from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Process-level health response."""

    status: str
    service: str
    environment: str


class ReadinessCheck(BaseModel):
    """Single dependency readiness check."""

    name: str
    status: str
    message: str | None = None


class ReadinessResponse(BaseModel):
    """Dependency readiness response."""

    model_config = ConfigDict(arbitrary_types_allowed=False)

    status: str
    checks: list[ReadinessCheck]

