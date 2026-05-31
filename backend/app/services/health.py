from __future__ import annotations

from collections.abc import Callable

import structlog
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.schemas.health import ReadinessCheck, ReadinessResponse

logger = structlog.get_logger(__name__)

SessionFactory = Callable[[], Session]


class HealthService:
    """Service that checks runtime dependencies."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def readiness(self) -> ReadinessResponse:
        """Check whether required dependencies are ready."""
        database_check = self._check_database()
        status = "ready" if database_check.status == "ready" else "not_ready"
        return ReadinessResponse(status=status, checks=[database_check])

    def _check_database(self) -> ReadinessCheck:
        try:
            with self._session_factory() as session:
                session.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            logger.warning("database_readiness_failed", error=str(exc))
            return ReadinessCheck(
                name="postgres",
                status="not_ready",
                message="database query failed",
            )

        return ReadinessCheck(name="postgres", status="ready")

