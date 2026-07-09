from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

DEMO_PREFIX = "[DEMO]"
DEMO_SUITE = "demo-seed-suite"
DEMO_SEED_KEY_FIELD = "demo_seed_key"

RunKind = Literal["general", "approval", "evaluation"]
ApprovalOutcome = Literal["approve", "reject"]
DeploymentAction = Literal["promote", "rollback", "deprecate"]


@dataclass(frozen=True)
class AgentSeed:
    key: str
    name: str
    owner: str
    description: str
    v1_name: str
    v1_prompt: str
    v1_model: str
    v1_default_tool: str
    v2_name: str
    v2_prompt: str
    v2_model: str
    v2_default_tool: str


@dataclass(frozen=True)
class RunSeed:
    key: str
    kind: RunKind
    agent_key: str
    version_key: str
    task: str
    tool_name: str
    tool_input: dict[str, Any]
    reviewed_by: str | None = None
    outcome: ApprovalOutcome | None = None


@dataclass(frozen=True)
class EvaluationSeed:
    key: str
    agent_key: str
    version_key: str


@dataclass(frozen=True)
class DeploymentSeed:
    key: str
    action: DeploymentAction
    agent_key: str
    source_version_key: str | None
    target_version_key: str | None
    reason: str


AGENT_SEEDS: list[AgentSeed] = [
    AgentSeed(
        key="customer_support",
        name="Customer Support Agent",
        owner="support-ops",
        description="Handles customer questions, account lookups, and response drafting.",
        v1_name="Baseline",
        v1_prompt="Help customers with account and product questions.",
        v1_model="claude-sonnet-4",
        v1_default_tool="browser",
        v2_name="Escalation Ready",
        v2_prompt="Handle escalations and draft customer-facing responses.",
        v2_model="claude-sonnet-4",
        v2_default_tool="email",
    ),
    AgentSeed(
        key="research",
        name="Research Assistant",
        owner="research",
        description="Summarizes internal documents and gathers supporting sources.",
        v1_name="Baseline",
        v1_prompt="Research topics and summarize the findings.",
        v1_model="claude-sonnet-4",
        v1_default_tool="browser",
        v2_name="Deep Research",
        v2_prompt="Dig through internal documents and gather evidence.",
        v2_model="claude-sonnet-4",
        v2_default_tool="terminal",
    ),
    AgentSeed(
        key="finance",
        name="Finance Assistant",
        owner="finance",
        description="Prepares finance summaries, file lookups, and report drafts.",
        v1_name="Baseline",
        v1_prompt="Review finance files and summarize key points.",
        v1_model="claude-sonnet-4",
        v1_default_tool="file",
        v2_name="Reporting",
        v2_prompt="Prepare finance summaries and reporting drafts.",
        v2_model="claude-sonnet-4",
        v2_default_tool="browser",
    ),
]

RUN_SEEDS: list[RunSeed] = [
    RunSeed(
        key="support_email_approval_01",
        kind="approval",
        agent_key="customer_support",
        version_key="baseline",
        task=f"{DEMO_PREFIX} support email approval 01",
        tool_name="email",
        tool_input={
            "to": "customer@example.com",
            "subject": "Status update on support request",
            "body": "Please approve the outbound support response.",
        },
        reviewed_by="support.manager@example.com",
        outcome="approve",
    ),
    RunSeed(
        key="support_terminal_approval_02",
        kind="approval",
        agent_key="customer_support",
        version_key="escalation_ready",
        task=f"{DEMO_PREFIX} support terminal approval 02",
        tool_name="terminal",
        tool_input={"command": "generate escalation summary"},
        reviewed_by="support.manager@example.com",
        outcome="approve",
    ),
    RunSeed(
        key="research_email_approval_03",
        kind="approval",
        agent_key="research",
        version_key="baseline",
        task=f"{DEMO_PREFIX} research email approval 03",
        tool_name="email",
        tool_input={
            "to": "research-lead@example.com",
            "subject": "Approval for research synthesis",
        },
        reviewed_by="research.lead@example.com",
        outcome="approve",
    ),
    RunSeed(
        key="finance_terminal_approval_04",
        kind="approval",
        agent_key="finance",
        version_key="baseline",
        task=f"{DEMO_PREFIX} finance terminal approval 04",
        tool_name="terminal",
        tool_input={"command": "publish finance summary"},
        reviewed_by="finance.controller@example.com",
        outcome="reject",
    ),
    RunSeed(
        key="finance_email_approval_05",
        kind="approval",
        agent_key="finance",
        version_key="reporting",
        task=f"{DEMO_PREFIX} finance email approval 05",
        tool_name="email",
        tool_input={
            "to": "audit@example.com",
            "subject": "Quarterly review package",
        },
        reviewed_by="finance.controller@example.com",
        outcome="reject",
    ),
    RunSeed(
        key="support_browser_success_01",
        kind="general",
        agent_key="customer_support",
        version_key="baseline",
        task=f"{DEMO_PREFIX} support browser success 01",
        tool_name="browser",
        tool_input={"query": "Example Domain support article"},
    ),
    RunSeed(
        key="support_browser_success_02",
        kind="general",
        agent_key="customer_support",
        version_key="baseline",
        task=f"{DEMO_PREFIX} support browser success 02",
        tool_name="browser",
        tool_input={"query": "customer refund policy"},
    ),
    RunSeed(
        key="support_browser_blocked_03",
        kind="general",
        agent_key="customer_support",
        version_key="baseline",
        task=f"{DEMO_PREFIX} support browser blocked 03",
        tool_name="browser",
        tool_input={"query": "customer retention report", "deny": True},
    ),
    RunSeed(
        key="support_browser_failed_04",
        kind="general",
        agent_key="customer_support",
        version_key="baseline",
        task=f"{DEMO_PREFIX} support browser failed 04",
        tool_name="browser",
        tool_input={"query": "fail-tool"},
    ),
    RunSeed(
        key="support_file_success_05",
        kind="general",
        agent_key="customer_support",
        version_key="baseline",
        task=f"{DEMO_PREFIX} support file success 05",
        tool_name="file",
        tool_input={"path": "pyproject.toml"},
    ),
    RunSeed(
        key="research_browser_success_06",
        kind="general",
        agent_key="research",
        version_key="baseline",
        task=f"{DEMO_PREFIX} research browser success 06",
        tool_name="browser",
        tool_input={"query": "documentation testing guide"},
    ),
    RunSeed(
        key="research_browser_success_07",
        kind="general",
        agent_key="research",
        version_key="baseline",
        task=f"{DEMO_PREFIX} research browser success 07",
        tool_name="browser",
        tool_input={"query": "documentation workflow notes"},
    ),
    RunSeed(
        key="research_browser_blocked_08",
        kind="general",
        agent_key="research",
        version_key="baseline",
        task=f"{DEMO_PREFIX} research browser blocked 08",
        tool_name="browser",
        tool_input={"query": "confidential partner notes", "deny": True},
    ),
    RunSeed(
        key="research_browser_failed_09",
        kind="general",
        agent_key="research",
        version_key="baseline",
        task=f"{DEMO_PREFIX} research browser failed 09",
        tool_name="browser",
        tool_input={"query": "fail-tool"},
    ),
    RunSeed(
        key="research_file_success_10",
        kind="general",
        agent_key="research",
        version_key="baseline",
        task=f"{DEMO_PREFIX} research file success 10",
        tool_name="file",
        tool_input={"path": "pyproject.toml"},
    ),
    RunSeed(
        key="finance_file_success_11",
        kind="general",
        agent_key="finance",
        version_key="baseline",
        task=f"{DEMO_PREFIX} finance file success 11",
        tool_name="file",
        tool_input={"path": "pyproject.toml"},
    ),
    RunSeed(
        key="finance_file_success_12",
        kind="general",
        agent_key="finance",
        version_key="baseline",
        task=f"{DEMO_PREFIX} finance file success 12",
        tool_name="file",
        tool_input={"path": "app/main.py"},
    ),
    RunSeed(
        key="finance_browser_success_13",
        kind="general",
        agent_key="finance",
        version_key="baseline",
        task=f"{DEMO_PREFIX} finance browser success 13",
        tool_name="browser",
        tool_input={"query": "quarterly close checklist"},
    ),
    RunSeed(
        key="finance_browser_blocked_14",
        kind="general",
        agent_key="finance",
        version_key="baseline",
        task=f"{DEMO_PREFIX} finance browser blocked 14",
        tool_name="browser",
        tool_input={"query": "sensitive ledger export", "deny": True},
    ),
    RunSeed(
        key="finance_browser_failed_15",
        kind="general",
        agent_key="finance",
        version_key="baseline",
        task=f"{DEMO_PREFIX} finance browser failed 15",
        tool_name="browser",
        tool_input={"query": "fail-tool"},
    ),
    RunSeed(
        key="finance_file_success_16",
        kind="general",
        agent_key="finance",
        version_key="baseline",
        task=f"{DEMO_PREFIX} finance file success 16",
        tool_name="file",
        tool_input={"path": "alembic.ini"},
    ),
    RunSeed(
        key="support_browser_success_17",
        kind="general",
        agent_key="customer_support",
        version_key="escalation_ready",
        task=f"{DEMO_PREFIX} support browser success 17",
        tool_name="browser",
        tool_input={"query": "customer onboarding checklist"},
    ),
    RunSeed(
        key="research_terminal_failed_18",
        kind="general",
        agent_key="research",
        version_key="deep_research",
        task=f"{DEMO_PREFIX} research terminal failed 18",
        tool_name="terminal",
        tool_input={"command": "fail-tool"},
    ),
    RunSeed(
        key="research_terminal_blocked_19",
        kind="general",
        agent_key="research",
        version_key="deep_research",
        task=f"{DEMO_PREFIX} research terminal blocked 19",
        tool_name="terminal",
        tool_input={"command": "prepare executive summary", "deny": True},
    ),
    RunSeed(
        key="finance_browser_success_20",
        kind="general",
        agent_key="finance",
        version_key="reporting",
        task=f"{DEMO_PREFIX} finance browser success 20",
        tool_name="browser",
        tool_input={"query": "expense variance summary"},
    ),
    RunSeed(
        key="finance_browser_success_21",
        kind="general",
        agent_key="finance",
        version_key="reporting",
        task=f"{DEMO_PREFIX} finance browser success 21",
        tool_name="browser",
        tool_input={"query": "budget tracking report"},
    ),
    RunSeed(
        key="support_file_failed_22",
        kind="general",
        agent_key="customer_support",
        version_key="escalation_ready",
        task=f"{DEMO_PREFIX} support file failed 22",
        tool_name="file",
        tool_input={"path": "missing-file.txt"},
    ),
    RunSeed(
        key="evaluation_support_baseline",
        kind="evaluation",
        agent_key="customer_support",
        version_key="baseline",
        task="demo-eval support baseline",
        tool_name="browser",
        tool_input={"query": "support demo evaluation"},
    ),
    RunSeed(
        key="evaluation_research_baseline",
        kind="evaluation",
        agent_key="research",
        version_key="baseline",
        task="demo-eval research baseline",
        tool_name="browser",
        tool_input={"query": "research demo evaluation"},
    ),
    RunSeed(
        key="evaluation_research_deep_research",
        kind="evaluation",
        agent_key="research",
        version_key="deep_research",
        task="demo-eval research deep research",
        tool_name="terminal",
        tool_input={"command": "demo evaluation"},
    ),
    RunSeed(
        key="evaluation_finance_baseline",
        kind="evaluation",
        agent_key="finance",
        version_key="baseline",
        task="demo-eval finance baseline",
        tool_name="file",
        tool_input={"path": "pyproject.toml"},
    ),
]

EVALUATION_SEEDS: list[EvaluationSeed] = [
    EvaluationSeed(
        key="eval_support_baseline",
        agent_key="customer_support",
        version_key="baseline",
    ),
    EvaluationSeed(
        key="eval_research_baseline",
        agent_key="research",
        version_key="baseline",
    ),
    EvaluationSeed(
        key="eval_research_deep_research",
        agent_key="research",
        version_key="deep_research",
    ),
    EvaluationSeed(
        key="eval_finance_baseline",
        agent_key="finance",
        version_key="baseline",
    ),
]

DEPLOYMENT_SEEDS: list[DeploymentSeed] = [
    DeploymentSeed(
        key="deploy_support_promote",
        action="promote",
        agent_key="customer_support",
        source_version_key=None,
        target_version_key="baseline",
        reason="demo seed: customer support production",
    ),
    DeploymentSeed(
        key="deploy_support_deprecate",
        action="deprecate",
        agent_key="customer_support",
        source_version_key="escalation_ready",
        target_version_key="escalation_ready",
        reason="demo seed: support escalation candidate retired",
    ),
    DeploymentSeed(
        key="deploy_research_promote_v1",
        action="promote",
        agent_key="research",
        source_version_key=None,
        target_version_key="baseline",
        reason="demo seed: research baseline promoted",
    ),
    DeploymentSeed(
        key="deploy_research_promote_v2",
        action="promote",
        agent_key="research",
        source_version_key="baseline",
        target_version_key="deep_research",
        reason="demo seed: research candidate rollout",
    ),
    DeploymentSeed(
        key="deploy_research_rollback",
        action="rollback",
        agent_key="research",
        source_version_key="deep_research",
        target_version_key="baseline",
        reason="demo seed: rollback to previous approved production version",
    ),
    DeploymentSeed(
        key="deploy_research_deprecate",
        action="deprecate",
        agent_key="research",
        source_version_key="deep_research",
        target_version_key="deep_research",
        reason="demo seed: research candidate retired",
    ),
    DeploymentSeed(
        key="deploy_finance_promote",
        action="promote",
        agent_key="finance",
        source_version_key=None,
        target_version_key="baseline",
        reason="demo seed: finance production",
    ),
]
