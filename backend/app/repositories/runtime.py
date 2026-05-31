from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models.agent import AgentVersion
from app.db.models.runtime import AgentRun, ToolCall, Trace
from app.domain.enums import AgentRunStatus, ToolCallStatus, TraceEventType


class RuntimeRepository:
    """Persistence operations for runtime execution data."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_agent_version(self, agent_version_id: uuid.UUID) -> AgentVersion | None:
        return self._session.get(AgentVersion, agent_version_id)

    def create_run(
        self,
        *,
        agent_id: uuid.UUID,
        agent_version_id: uuid.UUID,
        input_payload: dict[str, object],
        trace_id: str,
    ) -> AgentRun:
        run = AgentRun(
            agent_id=agent_id,
            agent_version_id=agent_version_id,
            input=input_payload,
            trace_id=trace_id,
        )
        self._session.add(run)
        self._session.flush()
        return run

    def list_runs(self, *, limit: int, offset: int) -> list[AgentRun]:
        statement: Select[tuple[AgentRun]] = (
            select(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit).offset(offset)
        )
        return list(self._session.scalars(statement).all())

    def get_run(self, run_id: uuid.UUID) -> AgentRun | None:
        return self._session.get(AgentRun, run_id)

    def get_run_for_update(self, run_id: uuid.UUID) -> AgentRun | None:
        statement = select(AgentRun).where(AgentRun.id == run_id).with_for_update()
        return self._session.scalars(statement).one_or_none()

    def get_tool_call(self, tool_call_id: uuid.UUID) -> ToolCall | None:
        return self._session.get(ToolCall, tool_call_id)

    def create_tool_call(
        self,
        *,
        agent_run_id: uuid.UUID,
        tool_name: str,
        input_payload: dict[str, object],
        trace_id: str,
        span_id: str,
    ) -> ToolCall:
        tool_call = ToolCall(
            agent_run_id=agent_run_id,
            tool_name=tool_name,
            input=input_payload,
            trace_id=trace_id,
            span_id=span_id,
        )
        self._session.add(tool_call)
        self._session.flush()
        return tool_call

    def create_trace(
        self,
        *,
        trace_id: str,
        event_type: TraceEventType,
        entity_type: str,
        name: str,
        attributes: dict[str, object],
        entity_id: uuid.UUID | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> Trace:
        trace = Trace(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            name=name,
            attributes=attributes,
        )
        self._session.add(trace)
        self._session.flush()
        return trace

    def mark_run_status(self, run: AgentRun, status: AgentRunStatus) -> None:
        run.status = status
        self._session.flush()

    def mark_tool_status(self, tool_call: ToolCall, status: ToolCallStatus) -> None:
        tool_call.status = status
        self._session.flush()

    def flush(self) -> None:
        self._session.flush()
