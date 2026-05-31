from __future__ import annotations

from app.tools.base import BaseTool, ToolResult


class BrowserTool(BaseTool):
    """Mock browser tool for MVP runtime execution."""

    name = "browser"

    def execute(self, tool_input: dict[str, object]) -> ToolResult:
        query = str(tool_input.get("query") or "")
        if bool(tool_input.get("force_failure")) or "fail-tool" in query:
            return ToolResult(
                success=False,
                error_message="browser mock failed",
                output={"query": query},
            )

        return ToolResult(
            success=True,
            output={
                "query": query,
                "summary": f"Mock browser result for: {query}",
            },
            token_count=max(1, len(query.split())),
        )
