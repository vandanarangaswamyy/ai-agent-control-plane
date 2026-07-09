#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _bootstrap() -> None:
    try:
        import sqlalchemy  # noqa: F401
    except Exception:  # noqa: BLE001
        venv_python = BACKEND_DIR / ".venv" / "bin" / "python"
        if venv_python.exists():
            os.execv(str(venv_python), [str(venv_python), str(Path(__file__).resolve()), *sys.argv[1:]])
        raise


_bootstrap()

from _demo_support import ApiClient

BASE_URL = os.getenv("DEMO_API_BASE_URL", "http://localhost:8000")


def main() -> int:
    print(f"Demo check against {BASE_URL}")

    summary = collect_summary_via_container()
    client = ApiClient(BASE_URL)

    checks = {
        "database reachable": bool(summary),
        "agents exist": summary.get("agents", 0) > 0,
        "versions exist": summary.get("versions", 0) > 0,
        "runs exist": summary.get("runs", 0) > 0,
        "traces exist": summary.get("traces", 0) > 0,
        "evaluations exist": summary.get("evaluations", 0) > 0,
        "deployments exist": summary.get("deployments", 0) > 0,
        "metrics endpoint responds": check_metrics_endpoint(client),
    }

    for label, result in checks.items():
        print(f"- {label}: {'ok' if result else 'fail'}")

    if all(checks.values()):
        print(
            "Summary: "
            f"{summary.get('agents', 0)} agents, "
            f"{summary.get('versions', 0)} versions, "
            f"{summary.get('runs', 0)} runs, "
            f"{summary.get('approvals', 0)} approvals, "
            f"{summary.get('evaluations', 0)} evaluations, "
            f"{summary.get('deployments', 0)} deployments, "
            f"{summary.get('traces', 0)} traces"
        )
        return 0

    return 1


def collect_summary_via_container() -> dict[str, int]:
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "api",
        "uv",
        "run",
        "python",
        "-c",
        "import json; from app.services.demo_seed import collect_demo_summary; print(json.dumps(collect_demo_summary()))",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            "unable to inspect demo data inside the backend container:\n"
            f"stdout: {completed.stdout}\n"
            f"stderr: {completed.stderr}"
        )

    return json.loads(completed.stdout.strip() or "{}")


def check_metrics_endpoint(client: ApiClient) -> bool:
    try:
        metrics_text = client.get_text("/metrics")
        return "agent_runs" in metrics_text and "tool_calls" in metrics_text
    except Exception:  # noqa: BLE001
        return False


if __name__ == "__main__":
    raise SystemExit(main())
