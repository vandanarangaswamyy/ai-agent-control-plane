from __future__ import annotations

from pathlib import Path

from app.tools.browser import BrowserTool
from app.tools.email import EmailTool
from app.tools.file import FileTool


def test_browser_tool_returns_realistic_mock_payload() -> None:
    result = BrowserTool().execute({"query": "Example Domain"})

    assert result.success is True
    assert result.output["title"] == "Example Domain"
    assert result.output["url"] == "https://example.com"
    assert result.output["status"] == "success"
    assert "summary" in result.output


def test_email_tool_returns_queue_payload() -> None:
    result = EmailTool().execute({"to": "demo@example.com", "subject": "Demo subject"})

    assert result.success is True
    assert result.output["to"] == "demo@example.com"
    assert result.output["subject"] == "Demo subject"
    assert result.output["status"] == "queued"
    assert result.output["provider"] == "mock"
    assert str(result.output["message_id"]).startswith("msg_")


def test_file_tool_returns_preview_payload(tmp_path: Path) -> None:
    file_path = tmp_path / "notes.txt"
    file_path.write_text("first line\nsecond line\nthird line", encoding="utf-8")

    result = FileTool(root=tmp_path).execute({"path": "notes.txt"})

    assert result.success is True
    assert result.output["path"] == "notes.txt"
    assert result.output["exists"] is True
    assert result.output["status"] == "success"
    assert "first line" in result.output["preview"]
