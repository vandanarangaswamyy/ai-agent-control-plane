from __future__ import annotations

import uuid

from app.db.session import SessionLocal
from app.repositories.runtime import RuntimeRepository
from app.services.runtime import RuntimeService
from app.tools.registry import ToolRegistry
from app.workers.celery_app import celery_app


@celery_app.task(name="runtime.execute_agent_run")
def execute_agent_run(run_id: str) -> dict[str, str]:
    """Execute an agent run from a Celery worker."""
    parsed_run_id = uuid.UUID(run_id)
    with SessionLocal() as session:
        service = RuntimeService(
            session=session,
            repository=RuntimeRepository(session=session),
            tool_registry=ToolRegistry(),
        )
        run = service.execute_run(parsed_run_id)
        return {"run_id": str(run.id), "status": run.status.value}
