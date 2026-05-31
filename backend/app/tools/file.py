from __future__ import annotations

from pathlib import Path

from app.tools.base import BaseTool, ToolResult


class FileTool(BaseTool):
    """Read-only file tool bounded to a configured root."""

    name = "file"

    def __init__(self, *, root: Path | None = None) -> None:
        self._root = (root or Path.cwd()).resolve()

    def execute(self, tool_input: dict[str, object]) -> ToolResult:
        raw_path = tool_input.get("path")
        if not raw_path:
            return ToolResult(success=False, error_message="file path is required")

        path = (self._root / str(raw_path)).resolve()
        if not path.is_relative_to(self._root):
            return ToolResult(success=False, error_message="file path is outside allowed root")
        if not path.is_file():
            return ToolResult(success=False, error_message="file does not exist")

        content = path.read_text(encoding="utf-8")
        return ToolResult(
            success=True,
            output={
                "path": str(path.relative_to(self._root)),
                "content": content,
            },
            token_count=max(1, len(content.split())),
        )
