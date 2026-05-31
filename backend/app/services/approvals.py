from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.approval import ApprovalRequest
from app.db.models.runtime import AgentRun, ToolCall
from app.domain.enums import AgentRunStatus, ApprovalStatus, ToolCallStatus, TraceEventType
from app.domain.errors import BusinessRuleViolationError, NotFoundError
from app.repositories.approvals import ApprovalRepository
from app.repositories.runtime import RuntimeRepository
from app.services.safety_gateway import SafetyGateway
from app.tools.base import ToolResult


class ApprovalService:
    """Business workflows for human approval requests."""

    def __init__(
        self,
        *,
        session: Session,
        approval_repository: ApprovalRepository,
        runtime_repository: RuntimeRepository,
        safety_gateway: SafetyGateway,
    ) -> None:
        self._session = session
        self._approval_repository = approval_repository
        self._runtime_repository = runtime_repository
        self._safety_gateway = safety_gateway

    def list_approval_requests(self, *, limit: int, offset: int) -> list[ApprovalRequest]:
        return self._approval_repository.list_approval_requests(limit=limit, offset=offset)

    def get_approval_request(self, approval_id: uuid.UUID) -> ApprovalRequest:
        approval = self._approval_repository.get_approval_request(approval_id)
        if approval is None:
            raise NotFoundError("approval request not found")
        return approval

    def approve(self, *, approval_id: uuid.UUID, reviewed_by: str | None = None) -> ApprovalRequest:
        approval = self._get_pending_approval_for_update(approval_id)
        run, tool_call = self._load_runtime_records(approval)

        approval.mark_reviewed(status=ApprovalStatus.APPROVED, reviewed_by=reviewed_by)
        run.status = AgentRunStatus.RUNNING
        run.error_message = None
        self._safety_gateway.trace_approval_event(
            run=run,
            tool_call=tool_call,
            event_name="ApprovalApproved",
            attributes={
                "approval_request_id": str(approval.id),
                "reviewed_by": reviewed_by,
            },
        )

        tool_result = self._safety_gateway.execute_approved_tool(run=run, tool_call=tool_call)
        self._finalize_run_after_tool(run=run, tool_call=tool_call, tool_result=tool_result)
        self._session.commit()
        self._session.refresh(approval)
        return approval

    def reject(self, *, approval_id: uuid.UUID, reviewed_by: str | None = None) -> ApprovalRequest:
        approval = self._get_pending_approval_for_update(approval_id)
        run, tool_call = self._load_runtime_records(approval)

        approval.mark_reviewed(status=ApprovalStatus.REJECTED, reviewed_by=reviewed_by)
        run.status = AgentRunStatus.BLOCKED
        run.error_message = "approval rejected"
        tool_call.status = ToolCallStatus.BLOCKED
        tool_call.error_message = "approval rejected"
        self._safety_gateway.trace_approval_event(
            run=run,
            tool_call=tool_call,
            event_name="ApprovalRejected",
            attributes={
                "approval_request_id": str(approval.id),
                "reviewed_by": reviewed_by,
            },
        )
        self._safety_gateway.trace_approval_event(
            run=run,
            tool_call=tool_call,
            event_name="ToolBlocked",
            attributes={
                "approval_request_id": str(approval.id),
                "reason": "approval rejected",
            },
        )
        self._session.commit()
        self._session.refresh(approval)
        return approval

    def _get_pending_approval_for_update(self, approval_id: uuid.UUID) -> ApprovalRequest:
        approval = self._approval_repository.get_approval_request_for_update(approval_id)
        if approval is None:
            raise NotFoundError("approval request not found")
        if approval.status != ApprovalStatus.PENDING:
            raise BusinessRuleViolationError("only PENDING approval requests can be reviewed")
        return approval

    def _load_runtime_records(self, approval: ApprovalRequest) -> tuple[AgentRun, ToolCall]:
        if approval.agent_run_id is None or approval.tool_call_id is None:
            raise BusinessRuleViolationError("approval request is missing runtime references")

        run = self._runtime_repository.get_run_for_update(approval.agent_run_id)
        tool_call = self._runtime_repository.get_tool_call(approval.tool_call_id)
        if run is None or tool_call is None:
            raise NotFoundError("approval runtime records not found")
        if run.status != AgentRunStatus.BLOCKED:
            raise BusinessRuleViolationError("approval can only resume a BLOCKED run")
        return run, tool_call

    def _finalize_run_after_tool(
        self,
        *,
        run: AgentRun,
        tool_call: ToolCall,
        tool_result: ToolResult,
    ) -> None:
        if not tool_result.success:
            run.status = AgentRunStatus.FAILED
            run.error_message = tool_result.error_message or "tool execution failed"
            run.token_count = tool_result.token_count
            run.estimated_cost = tool_result.estimated_cost
            run.end_time = _utc_now()
            run.latency_ms = _latency_ms(run.start_time, run.end_time)
            self._runtime_repository.create_trace(
                trace_id=run.trace_id or uuid.uuid4().hex,
                event_type=TraceEventType.AGENT_RUN,
                entity_type="agent_run",
                entity_id=run.id,
                name="AgentRunFailed",
                attributes={
                    "status": AgentRunStatus.FAILED.value,
                    "error_message": run.error_message,
                },
            )
            return

        run.output = {
            "task": str(run.input.get("task") or ""),
            "tool": tool_call.tool_name,
            "tool_output": tool_result.output,
        }
        run.token_count = tool_result.token_count
        run.estimated_cost = tool_result.estimated_cost or Decimal("0.000000")
        run.status = AgentRunStatus.SUCCESS
        run.end_time = _utc_now()
        run.latency_ms = _latency_ms(run.start_time, run.end_time)
        self._runtime_repository.create_trace(
            trace_id=run.trace_id or uuid.uuid4().hex,
            event_type=TraceEventType.AGENT_RUN,
            entity_type="agent_run",
            entity_id=run.id,
            name="AgentRunCompleted",
            attributes={
                "status": AgentRunStatus.SUCCESS.value,
                "latency_ms": run.latency_ms,
            },
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
