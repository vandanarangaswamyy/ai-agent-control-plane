from __future__ import annotations

from pathlib import Path

from app.tools.base import BaseTool
from app.tools.browser import BrowserTool
from app.tools.email import EmailTool
from app.tools.file import FileTool
from app.tools.terminal import TerminalTool


class ToolRegistry:
    """In-process registry for MVP runtime tools."""

    def __init__(self, *, file_root: Path | None = None) -> None:
        tools: list[BaseTool] = [
            BrowserTool(),
            EmailTool(),
            FileTool(root=file_root),
            TerminalTool(),
        ]
        self._tools = {tool.name: tool for tool in tools}

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)
