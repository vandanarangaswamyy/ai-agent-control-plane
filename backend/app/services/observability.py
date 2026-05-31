from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.db.models.approval import ApprovalRequest
from app.db.models.runtime import AgentRun, ToolCall, Trace
from app.domain.enums import ApprovalStatus, ToolCallStatus
from app.domain.errors import NotFoundError
from app.repositories.approvals import ApprovalRepository
from app.repositories.runtime import RuntimeRepository


@dataclass(frozen=True)
class TraceLookupResult:
    """Trace lookup payload assembled by the observability service."""

    trace_id: str
    events: list[Trace]


@dataclass(frozen=True)
class RunTimelineResult:
    """Timeline payload for a run."""

    run: AgentRun
    events: list[Trace]


@dataclass(frozen=True)
class RunFailureInspectionResult:
    """Failure analysis payload for a run."""

    run: AgentRun
    runtime_error_message: str | None
    failed_tool_calls: list[ToolCall]
    blocked_tool_calls: list[ToolCall]
    denied_policy_checks: list[Trace]
    approval_failures: list[ApprovalRequest]
    trace_events: list[Trace]


class ObservabilityService:
    """Query service for traces, timelines, and failure inspection."""

    _failure_event_names = {
        "AgentRunFailed",
        "ApprovalApproved",
        "ApprovalRejected",
        "ApprovalRequested",
        "PolicyCheck",
        "ToolBlocked",
        "ToolFailed",
        "ToolInvoked",
    }

    def __init__(
        self,
        *,
        runtime_repository: RuntimeRepository,
        approval_repository: ApprovalRepository,
    ) -> None:
        self._runtime_repository = runtime_repository
        self._approval_repository = approval_repository

    def get_trace(self, trace_id: str) -> TraceLookupResult:
        events = self._runtime_repository.list_traces_by_trace_id(trace_id)
        if not events:
            raise NotFoundError("trace not found")
        return TraceLookupResult(trace_id=trace_id, events=events)

    def get_run_timeline(self, run_id: uuid.UUID) -> RunTimelineResult:
        run = self._runtime_repository.get_run(run_id)
        if run is None:
            raise NotFoundError("agent run not found")

        trace_id = run.trace_id
        if trace_id is None:
            return RunTimelineResult(run=run, events=[])

        return RunTimelineResult(
            run=run,
            events=self._runtime_repository.list_traces_by_trace_id(trace_id),
        )

    def get_run_failures(self, run_id: uuid.UUID) -> RunFailureInspectionResult:
        run = self._runtime_repository.get_run(run_id)
        if run is None:
            raise NotFoundError("agent run not found")

        trace_events = self._timeline_events_for_run(run)
        tool_calls = self._runtime_repository.list_tool_calls_for_run(run_id)
        approvals = self._approval_repository.list_approval_requests_for_run(run_id)

        failed_tool_calls = [
            tool_call for tool_call in tool_calls if tool_call.status == ToolCallStatus.FAILED
        ]
        blocked_tool_calls = [
            tool_call for tool_call in tool_calls if tool_call.status == ToolCallStatus.BLOCKED
        ]
        denied_policy_checks = [
            event
            for event in trace_events
            if event.name == "PolicyCheck"
            and str(event.attributes.get("policy_decision", "")).upper() == "DENY"
        ]
        approval_failures = [
            approval
            for approval in approvals
            if approval.status in {ApprovalStatus.REJECTED, ApprovalStatus.EXPIRED}
        ]
        has_failures = any(
            (
                run.status.name in {"FAILED", "BLOCKED"},
                run.error_message,
                failed_tool_calls,
                blocked_tool_calls,
                denied_policy_checks,
                approval_failures,
            )
        )

        return RunFailureInspectionResult(
            run=run,
            runtime_error_message=run.error_message,
            failed_tool_calls=failed_tool_calls,
            blocked_tool_calls=blocked_tool_calls,
            denied_policy_checks=denied_policy_checks,
            approval_failures=approval_failures,
            trace_events=(
                [
                    event
                    for event in trace_events
                    if event.name in self._failure_event_names
                ]
                if has_failures
                else []
            ),
        )

    def _timeline_events_for_run(self, run: AgentRun) -> list[Trace]:
        if run.trace_id is None:
            return []
        return self._runtime_repository.list_traces_by_trace_id(run.trace_id)
