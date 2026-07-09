from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ApiResponse:
    """Minimal HTTP response wrapper used by the demo scripts."""

    status: int
    data: Any


class ApiClient:
    """Tiny JSON/HTTP client with no third-party dependencies."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def get_json(self, path: str) -> Any:
        return self._request_json("GET", path)

    def get_text(self, path: str) -> str:
        response = self._request("GET", path)
        return response.data.decode("utf-8")

    def post_json(self, path: str, payload: dict[str, Any]) -> Any:
        return self._request_json("POST", path, payload)

    def patch_json(self, path: str, payload: dict[str, Any]) -> Any:
        return self._request_json("PATCH", path, payload)

    def _request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        response = self._request(method, path, payload)
        if not response.data:
            return None
        return json.loads(response.data.decode("utf-8"))

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> ApiResponse:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"

        request = Request(
            url=f"{self._base_url}{path}",
            data=body,
            method=method,
            headers=headers,
        )

        try:
            with urlopen(request, timeout=30) as response:
                return ApiResponse(status=response.status, data=response.read())
        except HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"{method} {path} failed with {exc.code}: {body_text}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(f"{method} {path} failed: {exc.reason}") from exc


def wait_for_api(client: ApiClient, path: str = "/health", timeout_seconds: int = 60) -> None:
    """Poll the API until it is reachable."""

    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            response = client.get_json(path)
            if response is not None:
                return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(1)
    if last_error is not None:
        raise RuntimeError("backend API did not become ready") from last_error
    raise RuntimeError("backend API did not become ready")


def fetch_all_pages(
    client: ApiClient,
    path: str,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    """Fetch paginated list endpoints that accept limit/offset."""

    items: list[dict[str, Any]] = []
    offset = 0

    while True:
        query = f"{path}?limit={page_size}&offset={offset}"
        page = client.get_json(query)
        if not isinstance(page, list):
            raise RuntimeError(f"expected list response from {path}")
        items.extend(page)
        if len(page) < page_size:
            break
        offset += page_size

    return items
