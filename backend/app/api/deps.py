from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal, get_session
from app.services.health import HealthService


def get_app_settings() -> Settings:
    """Provide application settings through FastAPI dependency injection."""
    return get_settings()


def get_db_session() -> Generator[Session, None, None]:
    """Provide a request-scoped database session."""
    yield from get_session()


def get_health_service() -> HealthService:
    """Provide the health service with its database dependency."""
    return HealthService(session_factory=SessionLocal)

