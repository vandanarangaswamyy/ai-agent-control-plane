from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.runtime import AgentRun
from app.domain.enums import AgentRunStatus, PolicyDecision, TraceEventType
from app.domain.errors import BusinessRuleViolationError, NotFoundError
from app.repositories.runtime import RuntimeRepository
from app.services.safety_gateway import GatewayResult, SafetyGateway


class RuntimeService:
    """Execution engine for agent runs and tool calls."""

    def __init__(
        self,
        *,
        session: Session,
        repository: RuntimeRepository,
        safety_gateway: SafetyGateway,
    ) -> None:
        self._session = session
        self._repository = repository
        self._safety_gateway = safety_gateway

    def create_run(
        self,
        *,
        agent_version_id: uuid.UUID,
        task: str,
        tool_name: str | None = None,
        tool_input: dict[str, object] | None = None,
    ) -> AgentRun:
        agent_version = self._repository.get_agent_version(agent_version_id)
        if agent_version is None:
            raise NotFoundError("agent version not found")

        trace_id = uuid.uuid4().hex
        input_payload: dict[str, object] = {"task": task}
        if tool_name is not None:
            input_payload["tool_name"] = tool_name
        if tool_input is not None:
            input_payload["tool_input"] = tool_input

        run = self._repository.create_run(
            agent_id=agent_version.agent_id,
            agent_version_id=agent_version.id,
            input_payload=input_payload,
            trace_id=trace_id,
        )
        self._session.commit()
        self._session.refresh(run)
        return run

    def list_runs(self, *, limit: int, offset: int) -> list[AgentRun]:
        return self._repository.list_runs(limit=limit, offset=offset)

    def get_run(self, run_id: uuid.UUID) -> AgentRun:
        run = self._repository.get_run(run_id)
        if run is None:
            raise NotFoundError("agent run not found")
        return run

    def execute_run(self, run_id: uuid.UUID) -> AgentRun:
        run = self._repository.get_run_for_update(run_id)
        if run is None:
            raise NotFoundError("agent run not found")
        if run.status != AgentRunStatus.PENDING:
            raise BusinessRuleViolationError("only PENDING runs can be executed")

        run.status = AgentRunStatus.RUNNING
        run.start_time = _utc_now()
        self._trace(
            run=run,
            event_name="AgentRunStarted",
            attributes={"status": AgentRunStatus.RUNNING.value},
        )
        self._session.commit()

        try:
            tool_name = self._resolve_tool_name(run)
            tool_input = self._resolve_tool_input(run, tool_name)
            gateway_result = self._safety_gateway.invoke_tool(
                run=run,
                tool_name=tool_name,
                tool_input=tool_input,
            )

            self._apply_gateway_result(run=run, gateway_result=gateway_result)
            self._session.commit()
            self._session.refresh(run)
            return run
        except Exception as exc:
            self._session.rollback()
            failed_run = self._repository.get_run_for_update(run_id)
            if failed_run is None:
                raise

            failed_run.status = AgentRunStatus.FAILED
            failed_run.error_message = str(exc)
            failed_run.end_time = _utc_now()
            failed_run.latency_ms = _latency_ms(failed_run.start_time, failed_run.end_time)
            failed_run.token_count = failed_run.token_count or 0
            failed_run.estimated_cost = failed_run.estimated_cost or Decimal("0.000000")
            self._trace(
                run=failed_run,
                event_name="AgentRunFailed",
                attributes={
                    "status": AgentRunStatus.FAILED.value,
                    "error_message": failed_run.error_message,
                },
            )
            self._session.commit()
            self._session.refresh(failed_run)
            return failed_run

    def create_and_execute_run(
        self,
        *,
        agent_version_id: uuid.UUID,
        task: str,
        tool_name: str | None = None,
        tool_input: dict[str, object] | None = None,
    ) -> AgentRun:
        run = self.create_run(
            agent_version_id=agent_version_id,
            task=task,
            tool_name=tool_name,
            tool_input=tool_input,
        )
        return self.execute_run(run.id)

    def _apply_gateway_result(self, *, run: AgentRun, gateway_result: GatewayResult) -> None:
        if gateway_result.decision == PolicyDecision.REQUIRE_APPROVAL:
            run.status = AgentRunStatus.BLOCKED
            run.error_message = gateway_result.reason
            return

        if gateway_result.decision == PolicyDecision.DENY:
            run.status = AgentRunStatus.BLOCKED
            run.error_message = gateway_result.reason
            run.end_time = _utc_now()
            run.latency_ms = _latency_ms(run.start_time, run.end_time)
            return

        tool_result = gateway_result.tool_result
        if tool_result is None:
            raise RuntimeError("safety gateway did not return a tool result")

        if not tool_result.success:
            run.status = AgentRunStatus.FAILED
            run.error_message = tool_result.error_message or "tool execution failed"
            run.token_count = tool_result.token_count
            run.estimated_cost = tool_result.estimated_cost
            run.end_time = _utc_now()
            run.latency_ms = _latency_ms(run.start_time, run.end_time)
            self._trace(
                run=run,
                event_name="AgentRunFailed",
                attributes={
                    "status": AgentRunStatus.FAILED.value,
                    "error_message": run.error_message,
                },
            )
            return

        run.output = {
            "task": str(run.input.get("task") or ""),
            "tool": gateway_result.tool_call.tool_name,
            "tool_output": tool_result.output,
        }
        run.token_count = tool_result.token_count
        run.estimated_cost = tool_result.estimated_cost
        run.status = AgentRunStatus.SUCCESS
        run.end_time = _utc_now()
        run.latency_ms = _latency_ms(run.start_time, run.end_time)
        self._trace(
            run=run,
            event_name="AgentRunCompleted",
            attributes={
                "status": AgentRunStatus.SUCCESS.value,
                "latency_ms": run.latency_ms,
            },
        )

    def _resolve_tool_name(self, run: AgentRun) -> str:
        configured_tool = run.input.get("tool_name")
        if configured_tool:
            return str(configured_tool)

        agent_version = self._repository.get_agent_version(run.agent_version_id)
        tool_config = agent_version.tool_config if agent_version is not None else {}
        default_tool = tool_config.get("default_tool") if isinstance(tool_config, dict) else None
        return str(default_tool or "browser")

    def _resolve_tool_input(self, run: AgentRun, tool_name: str) -> dict[str, object]:
        explicit_input = run.input.get("tool_input")
        if isinstance(explicit_input, dict):
            return dict(explicit_input)

        task = str(run.input.get("task") or "")
        if tool_name == "browser":
            return {"query": task}
        if tool_name == "terminal":
            return {"command": f"echo {task}"}
        if tool_name == "email":
            return {"subject": task}
        if tool_name == "file":
            return {"path": task}
        return {"task": task}

    def _trace(
        self,
        *,
        run: AgentRun,
        event_name: str,
        attributes: dict[str, object],
    ) -> None:
        self._repository.create_trace(
            trace_id=run.trace_id or uuid.uuid4().hex,
            event_type=TraceEventType.AGENT_RUN,
            entity_type="agent_run",
            entity_id=run.id,
            name=event_name,
            attributes=attributes,
        )

def _utc_now() -> datetime:
    return datetime.now(UTC)


def _latency_ms(start_time: datetime | None, end_time: datetime | None) -> int | None:
    if start_time is None or end_time is None:
        return None
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=UTC)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=UTC)
    return max(0, int((end_time - start_time).total_seconds() * 1000))
