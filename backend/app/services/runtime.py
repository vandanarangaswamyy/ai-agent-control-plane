from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.runtime import AgentRun, ToolCall
from app.domain.enums import AgentRunStatus, ToolCallStatus, TraceEventType
from app.domain.errors import BusinessRuleViolationError, NotFoundError
from app.repositories.runtime import RuntimeRepository
from app.tools.base import BaseTool, ToolResult
from app.tools.registry import ToolRegistry


class RuntimeService:
    """Execution engine for agent runs and tool calls."""

    def __init__(
        self,
        *,
        session: Session,
        repository: RuntimeRepository,
        tool_registry: ToolRegistry,
    ) -> None:
        self._session = session
        self._repository = repository
        self._tool_registry = tool_registry

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
            tool = self._resolve_tool(tool_name)
            tool_input = self._resolve_tool_input(run, tool_name)
            tool_call, tool_result = self._invoke_tool(run=run, tool=tool, tool_input=tool_input)

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
                self._session.commit()
                self._session.refresh(run)
                return run

            run.output = {
                "task": str(run.input.get("task") or ""),
                "tool": tool_call.tool_name,
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

    def _invoke_tool(
        self,
        *,
        run: AgentRun,
        tool: BaseTool,
        tool_input: dict[str, object],
    ) -> tuple[ToolCall, ToolResult]:
        span_id = uuid.uuid4().hex
        tool_call = self._repository.create_tool_call(
            agent_run_id=run.id,
            tool_name=tool.name,
            input_payload=tool_input,
            trace_id=run.trace_id or uuid.uuid4().hex,
            span_id=span_id,
        )
        tool_call.status = ToolCallStatus.RUNNING
        tool_call.start_time = _utc_now()
        self._trace_tool(
            run=run,
            tool_call=tool_call,
            event_name="ToolInvoked",
            attributes={"tool_name": tool.name},
        )
        self._session.flush()

        try:
            result = tool.execute(tool_input)
        except Exception as exc:
            result = ToolResult(success=False, error_message=str(exc))

        tool_call.end_time = _utc_now()
        tool_call.latency_ms = _latency_ms(tool_call.start_time, tool_call.end_time)
        tool_call.output = result.output
        tool_call.error_message = result.error_message
        tool_call.status = ToolCallStatus.SUCCESS if result.success else ToolCallStatus.FAILED
        self._trace_tool(
            run=run,
            tool_call=tool_call,
            event_name="ToolSucceeded" if result.success else "ToolFailed",
            attributes={
                "tool_name": tool.name,
                "status": tool_call.status.value,
                "error_message": result.error_message,
            },
        )
        self._session.flush()
        return tool_call, result

    def _resolve_tool_name(self, run: AgentRun) -> str:
        configured_tool = run.input.get("tool_name")
        if configured_tool:
            return str(configured_tool)

        agent_version = self._repository.get_agent_version(run.agent_version_id)
        tool_config = agent_version.tool_config if agent_version is not None else {}
        default_tool = tool_config.get("default_tool") if isinstance(tool_config, dict) else None
        return str(default_tool or "browser")

    def _resolve_tool(self, tool_name: str) -> BaseTool:
        tool = self._tool_registry.get(tool_name)
        if tool is None:
            available = ", ".join(self._tool_registry.names())
            raise BusinessRuleViolationError(
                f"unknown tool '{tool_name}'. available tools: {available}"
            )
        return tool

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

    def _trace_tool(
        self,
        *,
        run: AgentRun,
        tool_call: ToolCall,
        event_name: str,
        attributes: dict[str, object],
    ) -> None:
        self._repository.create_trace(
            trace_id=run.trace_id or tool_call.trace_id or uuid.uuid4().hex,
            span_id=tool_call.span_id,
            event_type=TraceEventType.TOOL_CALL,
            entity_type="tool_call",
            entity_id=tool_call.id,
            name=event_name,
            attributes=attributes,
        )


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _latency_ms(start_time: datetime | None, end_time: datetime | None) -> int | None:
    if start_time is None or end_time is None:
        return None
    return max(0, int((end_time - start_time).total_seconds() * 1000))
