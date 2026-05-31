from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal, get_session
from app.repositories.agents import AgentRepository
from app.services.agent_registry import AgentRegistryService
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


def get_agent_registry_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> AgentRegistryService:
    """Provide the Agent Registry service."""
    repository = AgentRepository(session=session)
    return AgentRegistryService(session=session, repository=repository)
