from __future__ import annotations

from app.tools.base import BaseTool, ToolResult


class EmailTool(BaseTool):
    """Mock email tool for MVP runtime execution."""

    name = "email"

    def execute(self, tool_input: dict[str, object]) -> ToolResult:
        recipient = str(tool_input.get("to") or "mock@example.com")
        subject = str(tool_input.get("subject") or "Mock email")
        if bool(tool_input.get("force_failure")):
            return ToolResult(
                success=False,
                error_message="email mock failed",
                output={"to": recipient, "subject": subject},
            )

        return ToolResult(
            success=True,
            output={
                "to": recipient,
                "subject": subject,
                "sent": False,
                "mock": True,
            },
            token_count=max(1, len(subject.split())),
        )
