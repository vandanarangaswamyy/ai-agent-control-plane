from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.errors import (
    ApplicationError,
    BusinessRuleViolationError,
    ConflictError,
    InvalidStateTransitionError,
    NotFoundError,
)


def add_exception_handlers(app: FastAPI) -> None:
    """Register API exception handlers for service-layer errors."""

    @app.exception_handler(ApplicationError)
    async def application_error_handler(
        _request: Request,
        exc: ApplicationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=_status_code_for(exc),
            content={
                "error": {
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                }
            },
        )


def _status_code_for(exc: ApplicationError) -> int:
    if isinstance(exc, NotFoundError):
        return status.HTTP_404_NOT_FOUND
    if isinstance(exc, ConflictError | InvalidStateTransitionError):
        return status.HTTP_409_CONFLICT
    if isinstance(exc, BusinessRuleViolationError):
        return status.HTTP_422_UNPROCESSABLE_CONTENT
    return status.HTTP_500_INTERNAL_SERVER_ERROR
