from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.metrics import ObservabilityMetrics, get_observability_metrics
from app.db.session import SessionLocal, get_session
from app.repositories.agents import AgentRepository
from app.repositories.approvals import ApprovalRepository
from app.repositories.runtime import RuntimeRepository
from app.services.agent_registry import AgentRegistryService
from app.services.approvals import ApprovalService
from app.services.health import HealthService
from app.services.observability import ObservabilityService
from app.services.policy import PolicyEngine
from app.services.runtime import RuntimeService
from app.services.safety_gateway import SafetyGateway
from app.tools.registry import ToolRegistry


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


def get_runtime_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> RuntimeService:
    """Provide the Runtime service."""
    repository = RuntimeRepository(session=session)
    safety_gateway = _build_safety_gateway(session=session, runtime_repository=repository)
    return RuntimeService(
        session=session,
        repository=repository,
        safety_gateway=safety_gateway,
        metrics=get_observability_metrics(),
    )


def get_approval_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> ApprovalService:
    """Provide the Approval service."""
    runtime_repository = RuntimeRepository(session=session)
    approval_repository = ApprovalRepository(session=session)
    safety_gateway = _build_safety_gateway(
        session=session,
        runtime_repository=runtime_repository,
        approval_repository=approval_repository,
    )
    return ApprovalService(
        session=session,
        approval_repository=approval_repository,
        runtime_repository=runtime_repository,
        safety_gateway=safety_gateway,
        metrics=get_observability_metrics(),
    )


def get_observability_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> ObservabilityService:
    """Provide the observability query service."""
    runtime_repository = RuntimeRepository(session=session)
    approval_repository = ApprovalRepository(session=session)
    return ObservabilityService(
        runtime_repository=runtime_repository,
        approval_repository=approval_repository,
    )


def get_metrics_service() -> ObservabilityMetrics:
    """Provide the shared observability metrics registry."""
    return get_observability_metrics()


def _build_safety_gateway(
    *,
    session: Session,
    runtime_repository: RuntimeRepository,
    approval_repository: ApprovalRepository | None = None,
) -> SafetyGateway:
    return SafetyGateway(
        runtime_repository=runtime_repository,
        approval_repository=approval_repository or ApprovalRepository(session=session),
        tool_registry=ToolRegistry(),
        policy_engine=PolicyEngine(),
        metrics=get_observability_metrics(),
    )
