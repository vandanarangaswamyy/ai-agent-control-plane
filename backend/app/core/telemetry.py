from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Tracer

_SPAN_EXPORTER = InMemorySpanExporter()
_TRACE_PROVIDER: TracerProvider | None = None


def configure_telemetry(*, service_name: str) -> None:
    """Configure a local OpenTelemetry tracer provider once per process."""
    global _TRACE_PROVIDER
    if _TRACE_PROVIDER is not None:
        return

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(SimpleSpanProcessor(_SPAN_EXPORTER))
    trace.set_tracer_provider(provider)
    _TRACE_PROVIDER = provider


def get_tracer(name: str) -> Tracer:
    """Return a tracer for the given instrumentation namespace."""
    return trace.get_tracer(name)


def get_finished_spans() -> list[object]:
    """Return spans finished by the in-memory exporter."""
    return list(_SPAN_EXPORTER.get_finished_spans())


def reset_tracing() -> None:
    """Clear the in-memory span exporter between tests."""
    _SPAN_EXPORTER.clear()
