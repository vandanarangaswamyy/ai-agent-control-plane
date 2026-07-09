from __future__ import annotations

from urllib.parse import quote_plus

from app.tools.base import BaseTool, ToolResult


class BrowserTool(BaseTool):
    """Mock browser tool for MVP runtime execution."""

    name = "browser"

    def execute(self, tool_input: dict[str, object]) -> ToolResult:
        query = str(tool_input.get("query") or tool_input.get("url") or "")
        if bool(tool_input.get("force_failure")) or "fail-tool" in query:
            return ToolResult(
                success=False,
                error_message="browser mock failed",
                output={
                    "status": "failed",
                    "title": "Browser request failed",
                    "url": str(tool_input.get("url") or "https://example.com"),
                    "summary": "The mock browser could not complete the request.",
                },
            )

        url = str(tool_input.get("url") or _url_from_query(query))
        title = str(tool_input.get("title") or _title_from_query(query))
        return ToolResult(
            success=True,
            output={
                "title": title,
                "url": url,
                "summary": _summary_from_query(query),
                "status": "success",
            },
            token_count=max(1, len(query.split())),
        )


def _url_from_query(query: str) -> str:
    normalized = query.strip().lower() or "example-domain"
    slug = quote_plus(normalized.replace(" ", "-"))
    if "example" in normalized:
        return "https://example.com"
    return f"https://search.example.local/{slug}"


def _title_from_query(query: str) -> str:
    normalized = query.strip()
    if not normalized:
        return "Example Search Result"
    if "example" in normalized.lower():
        return "Example Domain"
    return normalized[:1].upper() + normalized[1:80]


def _summary_from_query(query: str) -> str:
    normalized = query.strip()
    if not normalized:
        return "Example Domain is a website used for documentation and testing."
    return (
        f"Mock browser result for '{normalized}'. "
        "This response is generated locally and never calls an external browser."
    )
