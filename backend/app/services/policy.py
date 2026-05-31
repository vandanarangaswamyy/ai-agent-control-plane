from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import PolicyDecision


@dataclass(frozen=True)
class PolicyResult:
    """Result of evaluating a tool execution policy."""

    decision: PolicyDecision
    reason: str


class PolicyEngine:
    """Configurable policy evaluator for tool execution."""

    def __init__(self, rules: dict[str, PolicyDecision] | None = None) -> None:
        self._rules = rules or {
            "browser": PolicyDecision.ALLOW,
            "email": PolicyDecision.REQUIRE_APPROVAL,
            "file": PolicyDecision.ALLOW,
            "terminal": PolicyDecision.REQUIRE_APPROVAL,
        }

    def evaluate(self, *, tool_name: str, tool_input: dict[str, object]) -> PolicyResult:
        if bool(tool_input.get("deny")):
            return PolicyResult(
                decision=PolicyDecision.DENY,
                reason="tool input requested denial",
            )

        decision = self._rules.get(tool_name, PolicyDecision.DENY)
        return PolicyResult(
            decision=decision,
            reason=f"default policy for {tool_name}: {decision.value}",
        )
