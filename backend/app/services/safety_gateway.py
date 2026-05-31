from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.metrics import ObservabilityMetrics, get_observability_metrics
from app.core.telemetry import get_tracer
from app.db.models.approval import ApprovalRequest
from app.db.models.runtime import AgentRun, ToolCall
from app.domain.enums import PolicyDecision, ToolCallStatus, TraceEventType
from app.domain.errors import BusinessRuleViolationError
from app.repositories.approvals import ApprovalRepository
from app.repositories.runtime import RuntimeRepository
from app.services.policy import PolicyEngine, PolicyResult
from app.tools.base import BaseTool, ToolResult
from app.tools.registry import ToolRegistry


@dataclass(frozen=True)
class GatewayResult:
    """Result of a safety-gated tool request."""

    decision: PolicyDecision
    tool_call: ToolCall
    tool_result: ToolResult | None = None
    approval_request: ApprovalRequest | None = None
    reason: str | None = None


class SafetyGateway:
    """Policy gate that sits between runtime execution and tool invocation."""

    def __init__(
        self,
        *,
        runtime_repository: RuntimeRepository,
        approval_repository: ApprovalRepository,
        tool_registry: ToolRegistry,
        policy_engine: PolicyEngine,
        metrics: ObservabilityMetrics | None = None,
    ) -> None:
        self._runtime_repository = runtime_repository
        self._approval_repository = approval_repository
        self._tool_registry = tool_registry
        self._policy_engine = policy_engine
        self._metrics = metrics or get_observability_metrics()

    def invoke_tool(
        self,
        *,
        run: AgentRun,
        tool_name: str,
        tool_input: dict[str, object],
    ) -> GatewayResult:
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("safety_gateway.invoke_tool") as span:
            span.set_attribute("run.id", str(run.id))
            span.set_attribute("tool.name", tool_name)

            tool = self._resolve_tool(tool_name)
            tool_call = self._runtime_repository.create_tool_call(
                agent_run_id=run.id,
                tool_name=tool.name,
                input_payload=tool_input,
                trace_id=run.trace_id or uuid.uuid4().hex,
                span_id=uuid.uuid4().hex,
            )
            self._metrics.record_tool_call_created()
            policy_result = self._policy_engine.evaluate(tool_name=tool.name, tool_input=tool_input)
            self._trace_policy_check(run=run, tool_call=tool_call, policy_result=policy_result)
            span.set_attribute("policy.decision", policy_result.decision.value)

            if policy_result.decision == PolicyDecision.ALLOW:
                result = self.execute_approved_tool(run=run, tool_call=tool_call)
                return GatewayResult(
                    decision=PolicyDecision.ALLOW,
                    tool_call=tool_call,
                    tool_result=result,
                    reason=policy_result.reason,
                )

            if policy_result.decision == PolicyDecision.REQUIRE_APPROVAL:
                tool_call.status = ToolCallStatus.BLOCKED
                tool_call.error_message = policy_result.reason
                approval = self._approval_repository.create_approval_request(
                    agent_run_id=run.id,
                    tool_call_id=tool_call.id,
                    reason=policy_result.reason,
                    requested_action={
                        "tool_name": tool.name,
                        "tool_input": tool_input,
                        "agent_run_id": str(run.id),
                    },
                )
                self._metrics.record_approval_requested()
                self._trace_policy_event(
                    run=run,
                    tool_call=tool_call,
                    event_name="ApprovalRequested",
                    attributes={
                        "approval_request_id": str(approval.id),
                        "policy_decision": policy_result.decision.value,
                        "reason": policy_result.reason,
                    },
                )
                self._trace_policy_event(
                    run=run,
                    tool_call=tool_call,
                    event_name="ToolBlocked",
                    attributes={
                        "policy_decision": policy_result.decision.value,
                        "reason": policy_result.reason,
                    },
                )
                return GatewayResult(
                    decision=PolicyDecision.REQUIRE_APPROVAL,
                    tool_call=tool_call,
                    approval_request=approval,
                    reason=policy_result.reason,
                )

            tool_call.status = ToolCallStatus.BLOCKED
            tool_call.error_message = policy_result.reason
            self._trace_policy_event(
                run=run,
                tool_call=tool_call,
                event_name="ToolBlocked",
                attributes={
                    "policy_decision": policy_result.decision.value,
                    "reason": policy_result.reason,
                },
            )
            return GatewayResult(
                decision=PolicyDecision.DENY,
                tool_call=tool_call,
                reason=policy_result.reason,
            )

    def execute_approved_tool(self, *, run: AgentRun, tool_call: ToolCall) -> ToolResult:
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("safety_gateway.execute_approved_tool") as span:
            tool = self._resolve_tool(tool_call.tool_name)
            tool_call.status = ToolCallStatus.RUNNING
            tool_call.start_time = _utc_now()
            tool_call.error_message = None
            self._trace_tool(
                run=run,
                tool_call=tool_call,
                event_name="ToolInvoked",
                attributes={"tool_name": tool.name},
            )
            self._runtime_repository.flush()

            try:
                with tracer.start_as_current_span("tool.execute") as tool_span:
                    tool_span.set_attribute("tool.name", tool.name)
                    result = tool.execute(tool_call.input)
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
            self._runtime_repository.flush()
            self._metrics.observe_tool_latency_ms(tool_call.latency_ms)
            if not result.success:
                self._metrics.record_tool_call_failed()
            span.set_attribute("tool.status", tool_call.status.value)
            return result

    def trace_approval_event(
        self,
        *,
        run: AgentRun,
        tool_call: ToolCall,
        event_name: str,
        attributes: dict[str, object],
    ) -> None:
        self._trace_policy_event(
            run=run,
            tool_call=tool_call,
            event_name=event_name,
            attributes=attributes,
        )

    def _resolve_tool(self, tool_name: str) -> BaseTool:
        tool = self._tool_registry.get(tool_name)
        if tool is None:
            available = ", ".join(self._tool_registry.names())
            raise BusinessRuleViolationError(
                f"unknown tool '{tool_name}'. available tools: {available}"
            )
        return tool

    def _trace_policy_check(
        self,
        *,
        run: AgentRun,
        tool_call: ToolCall,
        policy_result: PolicyResult,
    ) -> None:
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("safety_gateway.policy_check") as span:
            span.set_attribute("run.id", str(run.id))
            span.set_attribute("tool.name", tool_call.tool_name)
            span.set_attribute("policy.decision", policy_result.decision.value)
            self._trace_policy_event(
                run=run,
                tool_call=tool_call,
                event_name="PolicyCheck",
                attributes={
                    "tool_name": tool_call.tool_name,
                    "policy_decision": policy_result.decision.value,
                    "reason": policy_result.reason,
                },
            )

    def _trace_policy_event(
        self,
        *,
        run: AgentRun,
        tool_call: ToolCall,
        event_name: str,
        attributes: dict[str, object],
    ) -> None:
        self._runtime_repository.create_trace(
            trace_id=run.trace_id or tool_call.trace_id or uuid.uuid4().hex,
            span_id=tool_call.span_id,
            event_type=TraceEventType.POLICY_CHECK,
            entity_type="tool_call",
            entity_id=tool_call.id,
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
        self._runtime_repository.create_trace(
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
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=UTC)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=UTC)
    return max(0, int((end_time - start_time).total_seconds() * 1000))
