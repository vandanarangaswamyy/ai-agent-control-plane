from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class ToolResult:
    """Standard result returned by every tool."""

    success: bool
    output: dict[str, object] = field(default_factory=dict)
    error_message: str | None = None
    token_count: int = 0
    estimated_cost: Decimal = Decimal("0.000000")


class BaseTool(ABC):
    """Interface implemented by all runtime tools."""

    name: str

    @abstractmethod
    def execute(self, tool_input: dict[str, object]) -> ToolResult:
        """Execute the tool and return a standard result."""
