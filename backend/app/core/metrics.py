from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)


class ObservabilityMetrics:
    """Prometheus metrics registry for runtime and approval telemetry."""

    def __init__(self) -> None:
        self.registry = CollectorRegistry()

        self.agent_runs = Counter(
            "agent_runs",
            "Total agent runs created.",
            registry=self.registry,
        )
        self.agent_runs_success = Counter(
            "agent_runs_success",
            "Total successful agent runs.",
            registry=self.registry,
        )
        self.agent_runs_failed = Counter(
            "agent_runs_failed",
            "Total failed agent runs.",
            registry=self.registry,
        )
        self.agent_runs_blocked = Counter(
            "agent_runs_blocked",
            "Total blocked agent runs.",
            registry=self.registry,
        )
        self.tool_calls = Counter(
            "tool_calls",
            "Total tool calls created.",
            registry=self.registry,
        )
        self.tool_calls_failed = Counter(
            "tool_calls_failed",
            "Total failed tool calls.",
            registry=self.registry,
        )
        self.approval_requests = Counter(
            "approval_requests",
            "Total approval requests created.",
            registry=self.registry,
        )
        self.approval_requests_approved = Counter(
            "approval_requests_approved",
            "Total approval requests approved.",
            registry=self.registry,
        )
        self.approval_requests_rejected = Counter(
            "approval_requests_rejected",
            "Total approval requests rejected.",
            registry=self.registry,
        )
        self.agent_run_latency_seconds = Histogram(
            "agent_run_latency_seconds",
            "Observed agent run latency in seconds.",
            registry=self.registry,
        )
        self.tool_call_latency_seconds = Histogram(
            "tool_call_latency_seconds",
            "Observed tool call latency in seconds.",
            registry=self.registry,
        )

    def record_run_created(self) -> None:
        self.agent_runs.inc()

    def record_run_success(self) -> None:
        self.agent_runs_success.inc()

    def record_run_failed(self) -> None:
        self.agent_runs_failed.inc()

    def record_run_blocked(self) -> None:
        self.agent_runs_blocked.inc()

    def record_tool_call_created(self) -> None:
        self.tool_calls.inc()

    def record_tool_call_failed(self) -> None:
        self.tool_calls_failed.inc()

    def record_approval_requested(self) -> None:
        self.approval_requests.inc()

    def record_approval_approved(self) -> None:
        self.approval_requests_approved.inc()

    def record_approval_rejected(self) -> None:
        self.approval_requests_rejected.inc()

    def observe_run_latency_ms(self, latency_ms: int | None) -> None:
        if latency_ms is not None:
            self.agent_run_latency_seconds.observe(latency_ms / 1000)

    def observe_tool_latency_ms(self, latency_ms: int | None) -> None:
        if latency_ms is not None:
            self.tool_call_latency_seconds.observe(latency_ms / 1000)

    def render(self) -> bytes:
        return generate_latest(self.registry)

    @property
    def content_type(self) -> str:
        return CONTENT_TYPE_LATEST


_METRICS = ObservabilityMetrics()


def get_observability_metrics() -> ObservabilityMetrics:
    return _METRICS


def reset_observability_metrics() -> None:
    global _METRICS
    _METRICS = ObservabilityMetrics()
