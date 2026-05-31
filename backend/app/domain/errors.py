from __future__ import annotations


class ApplicationError(Exception):
    """Base application exception for service-layer errors."""

    message = "application error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(ApplicationError):
    """Raised when a requested domain resource does not exist."""

    message = "resource not found"


class ConflictError(ApplicationError):
    """Raised when a request conflicts with existing persisted state."""

    message = "resource conflict"


class InvalidStateTransitionError(ApplicationError):
    """Raised when a lifecycle transition is not allowed."""

    message = "invalid lifecycle transition"


class BusinessRuleViolationError(ApplicationError):
    """Raised when a request violates a domain rule."""

    message = "business rule violation"
