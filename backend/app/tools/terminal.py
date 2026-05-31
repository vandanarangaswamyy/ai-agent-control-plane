from __future__ import annotations

from app.tools.base import BaseTool, ToolResult


class TerminalTool(BaseTool):
    """Sandboxed terminal mock that never executes commands."""

    name = "terminal"

    def execute(self, tool_input: dict[str, object]) -> ToolResult:
        command = str(tool_input.get("command") or "")
        if not command:
            return ToolResult(success=False, error_message="command is required")
        if bool(tool_input.get("force_failure")) or "fail-tool" in command:
            return ToolResult(
                success=False,
                error_message="terminal mock failed",
                output={"command": command, "executed": False},
            )

        return ToolResult(
            success=True,
            output={
                "command": command,
                "executed": False,
                "stdout": f"mock terminal output for: {command}",
            },
            token_count=max(1, len(command.split())),
        )
