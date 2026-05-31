from __future__ import annotations

import uuid

from app.db.session import SessionLocal
from app.repositories.approvals import ApprovalRepository
from app.repositories.runtime import RuntimeRepository
from app.services.policy import PolicyEngine
from app.services.runtime import RuntimeService
from app.services.safety_gateway import SafetyGateway
from app.tools.registry import ToolRegistry
from app.workers.celery_app import celery_app


@celery_app.task(name="runtime.execute_agent_run")
def execute_agent_run(run_id: str) -> dict[str, str]:
    """Execute an agent run from a Celery worker."""
    parsed_run_id = uuid.UUID(run_id)
    with SessionLocal() as session:
        runtime_repository = RuntimeRepository(session=session)
        safety_gateway = SafetyGateway(
            runtime_repository=runtime_repository,
            approval_repository=ApprovalRepository(session=session),
            tool_registry=ToolRegistry(),
            policy_engine=PolicyEngine(),
        )
        service = RuntimeService(
            session=session,
            repository=runtime_repository,
            safety_gateway=safety_gateway,
        )
        run = service.execute_run(parsed_run_id)
        return {"run_id": str(run.id), "status": run.status.value}
