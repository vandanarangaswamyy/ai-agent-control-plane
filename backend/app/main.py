from __future__ import annotations

from time import perf_counter

from fastapi import FastAPI, Request

from app.api.errors import add_exception_handlers
from app.api.metrics import router as metrics_router
from app.api.v1.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.telemetry import configure_telemetry, get_tracer


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(settings=settings)
    configure_telemetry(service_name=settings.otel_service_name)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    add_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix="/api/v1")
    app.include_router(metrics_router)

    @app.middleware("http")
    async def trace_requests(request: Request, call_next):
        tracer = get_tracer("app.http")
        span_name = f"HTTP {request.method} {request.url.path}"
        started = perf_counter()
        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.target", request.url.path)
            span.set_attribute("http.client_ip", request.client.host if request.client else "")
            try:
                response = await call_next(request)
            except Exception as exc:
                span.record_exception(exc)
                span.set_attribute("http.duration_ms", int((perf_counter() - started) * 1000))
                raise
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.duration_ms", int((perf_counter() - started) * 1000))
            return response

    return app


app = create_app()
