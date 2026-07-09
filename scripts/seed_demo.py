#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from _demo_support import ApiClient, fetch_all_pages, wait_for_api
from seed_manifest import (
    AGENT_SEEDS,
    DEMO_SEED_KEY_FIELD,
    DEMO_SUITE,
    DEPLOYMENT_SEEDS,
    DeploymentSeed,
    EVALUATION_SEEDS,
    RUN_SEEDS,
    RunSeed,
)

ROOT = Path(__file__).resolve().parents[1]


def _bootstrap() -> None:
    try:
        import sqlalchemy  # noqa: F401
    except Exception:  # noqa: BLE001
        backend_dir = Path(__file__).resolve().parents[1] / "backend"
        venv_python = backend_dir / ".venv" / "bin" / "python"
        if venv_python.exists():
            os.execv(
                str(venv_python),
                [str(venv_python), str(Path(__file__).resolve()), *sys.argv[1:]],
            )
        raise


_bootstrap()

BASE_URL = os.getenv("DEMO_API_BASE_URL", "http://localhost:8000")


def main() -> None:
    client = ApiClient(BASE_URL)
    wait_for_api(client)

    print(f"Seeding demo data via {BASE_URL}")

    agent_map = ensure_agents(client)
    version_map = ensure_versions(client, agent_map)

    apply_demo_timestamps()

    ensure_runs(client, version_map)
    ensure_evaluations(client, version_map)
    ensure_deployments(client, version_map)

    apply_demo_timestamps()
    print_summary(client)


def ensure_agents(client: ApiClient) -> dict[str, dict[str, Any]]:
    existing_agents = {
        agent["name"]: agent for agent in fetch_all_pages(client, "/api/v1/agents")
    }
    agent_map: dict[str, dict[str, Any]] = {}

    for seed in AGENT_SEEDS:
        agent = existing_agents.get(seed.name)
        if agent is None:
            agent = client.post_json(
                "/api/v1/agents",
                {
                    "name": seed.name,
                    "description": seed.description,
                    "owner": seed.owner,
                },
            )
            existing_agents[seed.name] = agent
        agent_map[seed.key] = agent

    return agent_map


def ensure_versions(
    client: ApiClient,
    agent_map: dict[str, dict[str, Any]],
) -> dict[str, dict[str, dict[str, Any]]]:
    version_map: dict[str, dict[str, dict[str, Any]]] = {}

    for seed in AGENT_SEEDS:
        agent = agent_map[seed.key]
        versions = fetch_all_pages(client, f"/api/v1/agents/{agent['id']}/versions")
        by_name = {
            version["name"]: version
            for version in versions
            if version["name"] is not None
        }
        seed_versions: dict[str, dict[str, Any]] = {}

        for version_key, name, prompt, model, default_tool in (
            (
                "baseline",
                seed.v1_name,
                seed.v1_prompt,
                seed.v1_model,
                seed.v1_default_tool,
            ),
            (
                "escalation_ready",
                seed.v2_name,
                seed.v2_prompt,
                seed.v2_model,
                seed.v2_default_tool,
            ),
        ):
            version = by_name.get(name)
            if version is None:
                version = client.post_json(
                    f"/api/v1/agents/{agent['id']}/versions",
                    {
                        "name": name,
                        "prompt": prompt,
                        "model": model,
                        "tool_config": {"default_tool": default_tool},
                        "runtime_config": {"temperature": 0},
                    },
                )
                versions.append(version)
            seed_versions[version_key] = version

        # Newer manifest keys for the extra finance/research demo versions.
        if seed.key == "research":
            seed_versions["deep_research"] = _ensure_version(
                client=client,
                versions=versions,
                agent_id=agent["id"],
                name="Deep Research",
                prompt="Dig through internal documents and gather evidence.",
                model="claude-sonnet-4",
                default_tool="terminal",
            )
        if seed.key == "finance":
            seed_versions["reporting"] = _ensure_version(
                client=client,
                versions=versions,
                agent_id=agent["id"],
                name="Reporting",
                prompt="Prepare finance summaries and reporting drafts.",
                model="claude-sonnet-4",
                default_tool="browser",
            )

        version_map[seed.key] = seed_versions

    return version_map


def _ensure_version(
    *,
    client: ApiClient,
    versions: list[dict[str, Any]],
    agent_id: str,
    name: str,
    prompt: str,
    model: str,
    default_tool: str,
) -> dict[str, Any]:
    by_name = {
        version["name"]: version for version in versions if version["name"] is not None
    }
    version = by_name.get(name)
    if version is not None:
        return version

    version = client.post_json(
        f"/api/v1/agents/{agent_id}/versions",
        {
            "name": name,
            "prompt": prompt,
            "model": model,
            "tool_config": {"default_tool": default_tool},
            "runtime_config": {"temperature": 0},
        },
    )
    versions.append(version)
    return version


def ensure_runs(
    client: ApiClient,
    version_map: dict[str, dict[str, dict[str, Any]]],
) -> None:
    runs = fetch_all_pages(client, "/api/v1/runs")
    existing_by_key = {
        _run_seed_key(run): run for run in runs if _run_seed_key(run) is not None
    }

    for seed in RUN_SEEDS:
        version = version_map[seed.agent_key][seed.version_key]
        run = existing_by_key.get(seed.key)
        if run is None:
            run = client.post_json(
                "/api/v1/runs",
                {
                    "agent_version_id": version["id"],
                    "task": seed.task,
                    "tool_name": seed.tool_name,
                    "tool_input": _tool_input_for_seed(seed),
                },
            )
            existing_by_key[seed.key] = run

        if seed.kind == "approval":
            approval = find_approval_for_run(client, run["id"])
            if approval["status"] == "PENDING":
                action = "approve" if seed.outcome == "approve" else "reject"
                client.post_json(
                    f"/api/v1/approvals/{approval['id']}/{action}",
                    {"reviewed_by": seed.reviewed_by},
                )


def ensure_evaluations(
    client: ApiClient,
    version_map: dict[str, dict[str, dict[str, Any]]],
) -> None:
    evaluations = fetch_all_pages(client, "/api/v1/evaluations")
    existing_keys = {
        (str(evaluation["agent_version_id"]), str(evaluation["suite_name"]))
        for evaluation in evaluations
    }

    for seed in EVALUATION_SEEDS:
        version = version_map[seed.agent_key][seed.version_key]
        key = (str(version["id"]), DEMO_SUITE)
        if key in existing_keys:
            continue
        client.post_json(
            "/api/v1/evaluations",
            {
                "agent_version_id": version["id"],
                "suite_name": DEMO_SUITE,
            },
        )


def ensure_deployments(
    client: ApiClient,
    version_map: dict[str, dict[str, dict[str, Any]]],
) -> None:
    for seed in DEPLOYMENT_SEEDS:
        agent = version_map[seed.agent_key][seed.target_version_key or "baseline"][
            "agent_id"
        ]
        history = fetch_all_pages(client, f"/api/v1/agents/{agent}/deployments")
        if _deployment_exists(history, seed, version_map):
            continue
        _apply_deployment_step(client, seed, version_map)


def _apply_deployment_step(
    client: ApiClient,
    seed: DeploymentSeed,
    version_map: dict[str, dict[str, dict[str, Any]]],
) -> None:
    agent_id = version_map[seed.agent_key]["baseline"]["agent_id"]
    if seed.action == "promote":
        target_version = version_map[seed.agent_key][
            seed.target_version_key or "baseline"
        ]
        if target_version["lifecycle"] == "PRODUCTION":
            return
        client.post_json(
            "/api/v1/deployments/promote",
            {
                "agent_id": agent_id,
                "agent_version_id": target_version["id"],
                "reason": seed.reason,
            },
        )
        return

    if seed.action == "rollback":
        client.post_json(
            "/api/v1/deployments/rollback",
            {
                "agent_id": agent_id,
                "reason": seed.reason,
            },
        )
        return

    target_version = version_map[seed.agent_key][seed.target_version_key or "baseline"]
    if target_version["lifecycle"] == "DEPRECATED":
        return
    client.post_json(
        f"/api/v1/agents/{agent_id}/versions/{target_version['id']}/deprecate",
        {},
    )


def _deployment_exists(
    history: list[dict[str, Any]],
    seed: DeploymentSeed,
    version_map: dict[str, dict[str, dict[str, Any]]],
) -> bool:
    agent_id = version_map[seed.agent_key]["baseline"]["agent_id"]
    target_id = version_map[seed.agent_key][seed.target_version_key or "baseline"]["id"]
    source_id = (
        version_map[seed.agent_key][seed.source_version_key]["id"]
        if seed.source_version_key is not None
        else None
    )

    for event in history:
        if event["event_type"] != seed.action.upper():
            continue
        if event["agent_id"] != agent_id:
            continue
        if seed.action == "rollback":
            if (
                event["source_version_id"] == source_id
                and event["target_version_id"] == target_id
            ):
                return True
        elif seed.action == "promote":
            if event["target_version_id"] == target_id:
                return True
        elif seed.action == "deprecate":
            if event["target_version_id"] == target_id:
                return True

    return False


def find_approval_for_run(client: ApiClient, run_id: str) -> dict[str, Any]:
    approvals = fetch_all_pages(client, "/api/v1/approvals")
    for approval in approvals:
        if approval["agent_run_id"] == run_id:
            return approval
    raise RuntimeError(f"approval request not found for demo run {run_id}")


def _tool_input_for_seed(seed: RunSeed) -> dict[str, Any]:
    return {**seed.tool_input, DEMO_SEED_KEY_FIELD: seed.key}


def _run_seed_key(run: dict[str, Any]) -> str | None:
    tool_input = run.get("input", {}).get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    value = tool_input.get(DEMO_SEED_KEY_FIELD)
    return str(value) if value else None


def print_summary(client: ApiClient) -> None:
    agents = fetch_all_pages(client, "/api/v1/agents")
    versions = sum(
        len(fetch_all_pages(client, f"/api/v1/agents/{agent['id']}/versions"))
        for agent in agents
    )
    runs = fetch_all_pages(client, "/api/v1/runs")
    approvals = fetch_all_pages(client, "/api/v1/approvals")
    evaluations = fetch_all_pages(client, "/api/v1/evaluations")
    deployments = sum(
        len(client.get_json(f"/api/v1/agents/{agent['id']}/deployments"))
        for agent in agents
    )

    print("Demo seed complete:")
    print(f"  agents: {len(agents)}")
    print(f"  versions: {versions}")
    print(f"  runs: {len(runs)}")
    print(f"  approvals: {len(approvals)}")
    print(f"  evaluations: {len(evaluations)}")
    print(f"  deployments: {deployments}")


def apply_demo_timestamps() -> None:
    """Normalize demo timestamps and backfill stable seed keys inside the backend container."""

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
        "from app.services.demo_seed import apply_demo_timestamps; print(apply_demo_timestamps())",
    ]
    completed = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "unable to normalize demo timestamps inside the backend container:\n"
            f"stdout: {completed.stdout}\n"
            f"stderr: {completed.stderr}"
        )
    if completed.stdout.strip():
        print(completed.stdout.strip())


if __name__ == "__main__":
    main()
