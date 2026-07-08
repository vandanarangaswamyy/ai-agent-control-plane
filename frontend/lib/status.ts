import type {
  ApprovalStatus,
  AgentRunStatus,
  AgentVersionLifecycle,
  DeploymentEventType,
  EvaluationResultStatus,
  EvaluationStatus,
  PolicyDecision,
  ToolCallStatus,
  TraceEventType,
} from "@/lib/api/types";
import type { BadgeProps } from "@/components/ui/badge";

type BadgeVariant = NonNullable<BadgeProps["variant"]>;

export function runStatusVariant(status: AgentRunStatus): BadgeVariant {
  switch (status) {
    case "SUCCESS":
      return "success";
    case "FAILED":
      return "destructive";
    case "BLOCKED":
      return "warning";
    case "RUNNING":
      return "secondary";
    case "PENDING":
    default:
      return "outline";
  }
}

export function toolStatusVariant(status: ToolCallStatus): BadgeVariant {
  switch (status) {
    case "SUCCESS":
      return "success";
    case "FAILED":
      return "destructive";
    case "BLOCKED":
      return "warning";
    case "RUNNING":
      return "secondary";
    case "PENDING":
    default:
      return "outline";
  }
}

export function lifecycleVariant(status: AgentVersionLifecycle): BadgeVariant {
  switch (status) {
    case "PRODUCTION":
      return "success";
    case "APPROVED":
      return "secondary";
    case "EVALUATED":
      return "default";
    case "DEPRECATED":
      return "destructive";
    case "DRAFT":
    default:
      return "outline";
  }
}

export function approvalStatusVariant(status: ApprovalStatus): BadgeVariant {
  switch (status) {
    case "APPROVED":
      return "success";
    case "REJECTED":
      return "destructive";
    case "EXPIRED":
      return "warning";
    case "PENDING":
    default:
      return "outline";
  }
}

export function evaluationStatusVariant(status: EvaluationStatus): BadgeVariant {
  switch (status) {
    case "PASSED":
      return "success";
    case "FAILED":
      return "destructive";
    case "RUNNING":
      return "secondary";
    case "PENDING":
    default:
      return "outline";
  }
}

export function evaluationResultVariant(status: EvaluationResultStatus): BadgeVariant {
  return status === "PASSED" ? "success" : "destructive";
}

export function deploymentEventVariant(status: DeploymentEventType): BadgeVariant {
  switch (status) {
    case "PROMOTE":
      return "success";
    case "ROLLBACK":
      return "warning";
    case "DEPRECATE":
    default:
      return "destructive";
  }
}

export function policyDecisionVariant(status: PolicyDecision): BadgeVariant {
  switch (status) {
    case "ALLOW":
      return "success";
    case "REQUIRE_APPROVAL":
      return "warning";
    case "DENY":
    default:
      return "destructive";
  }
}

export function traceEventVariant(status: TraceEventType): BadgeVariant {
  switch (status) {
    case "AGENT_RUN":
      return "secondary";
    case "TOOL_CALL":
      return "default";
    case "POLICY_CHECK":
      return "warning";
    case "EVALUATION":
      return "secondary";
    case "DEPLOYMENT":
    default:
      return "success";
  }
}

