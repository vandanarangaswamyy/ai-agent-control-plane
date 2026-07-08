export type AgentVersionLifecycle =
  | "DRAFT"
  | "EVALUATED"
  | "APPROVED"
  | "PRODUCTION"
  | "DEPRECATED";

export type AgentRunStatus = "PENDING" | "RUNNING" | "SUCCESS" | "FAILED" | "BLOCKED";
export type ToolCallStatus = "PENDING" | "RUNNING" | "SUCCESS" | "FAILED" | "BLOCKED";
export type PolicyDecision = "ALLOW" | "REQUIRE_APPROVAL" | "DENY";
export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED";
export type EvaluationStatus = "PENDING" | "RUNNING" | "PASSED" | "FAILED";
export type EvaluationResultStatus = "PASSED" | "FAILED";
export type DeploymentEventType = "PROMOTE" | "ROLLBACK" | "DEPRECATE";
export type TraceEventType =
  | "AGENT_RUN"
  | "TOOL_CALL"
  | "POLICY_CHECK"
  | "EVALUATION"
  | "DEPLOYMENT";

export interface AgentRead {
  id: string;
  name: string;
  description: string | null;
  owner: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentVersionRead {
  id: string;
  agent_id: string;
  version: number;
  name: string | null;
  prompt: string;
  model: string;
  tool_config: Record<string, unknown>;
  runtime_config: Record<string, unknown>;
  lifecycle: AgentVersionLifecycle;
  created_at: string;
  updated_at: string;
}

export interface RunRead {
  id: string;
  agent_id: string;
  agent_version_id: string;
  status: AgentRunStatus;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  error_message: string | null;
  start_time: string | null;
  end_time: string | null;
  latency_ms: number | null;
  token_count: number | null;
  estimated_cost: string | number | null;
  trace_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ToolCallRead {
  id: string;
  agent_run_id: string;
  tool_name: string;
  status: ToolCallStatus;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  error_message: string | null;
  start_time: string | null;
  end_time: string | null;
  latency_ms: number | null;
  trace_id: string | null;
  span_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface TraceEventRead {
  id: string;
  trace_id: string;
  span_id: string | null;
  parent_span_id: string | null;
  event_type: TraceEventType;
  entity_type: string;
  entity_id: string | null;
  name: string;
  attributes: Record<string, unknown>;
  timestamp: string;
}

export interface TraceLookupRead {
  trace_id: string;
  events: TraceEventRead[];
}

export interface RunTimelineRead {
  run: RunRead;
  events: TraceEventRead[];
}

export interface RunFailureInspectionRead {
  run: RunRead;
  runtime_error_message: string | null;
  failed_tool_calls: ToolCallRead[];
  blocked_tool_calls: ToolCallRead[];
  denied_policy_checks: TraceEventRead[];
  approval_failures: ApprovalRequestRead[];
  trace_events: TraceEventRead[];
}

export interface ApprovalRequestRead {
  id: string;
  agent_run_id: string | null;
  tool_call_id: string | null;
  policy_decision: PolicyDecision;
  reason: string;
  requested_action: Record<string, unknown>;
  status: ApprovalStatus;
  requested_by: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DeploymentEventRead {
  id: string;
  agent_id: string;
  event_type: DeploymentEventType;
  source_version_id: string | null;
  target_version_id: string | null;
  reason: string | null;
  trace_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface DeploymentPromotionRead {
  agent_id: string;
  version_promoted: string;
  previous_production_version: string | null;
  deployment_timestamp: string;
}

export interface DeploymentRollbackRead {
  agent_id: string;
  version_restored: string;
  rollback_timestamp: string;
}

export interface EvaluationSuiteCase {
  name: string;
  task: string;
  tool_name?: string | null;
  expected_tool_name?: string | null;
}

export interface EvaluationSuiteDefinition {
  name: string;
  cases: EvaluationSuiteCase[];
}

export interface EvaluationRead {
  id: string;
  agent_version_id: string;
  suite_name: string;
  status: EvaluationStatus;
  trace_id: string | null;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  total_cases: number | null;
  passed_cases: number | null;
  failed_cases: number | null;
  success_rate: string | number | null;
  tool_accuracy: string | number | null;
  average_latency_ms: number | null;
  total_cost: string | number | null;
  failure_rate: string | number | null;
  created_at: string;
  updated_at: string;
}

export interface EvaluationResultRead {
  id: string;
  evaluation_id: string;
  case_name: string;
  task: string;
  status: EvaluationResultStatus;
  run_id: string | null;
  tool_call_id: string | null;
  expected_tool_name: string | null;
  actual_tool_name: string | null;
  output: Record<string, unknown> | null;
  error_message: string | null;
  latency_ms: number | null;
  token_count: number | null;
  estimated_cost: string | number | null;
  trace_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface EvaluationReportRead {
  evaluation: EvaluationRead;
  suite: EvaluationSuiteDefinition;
  results: EvaluationResultRead[];
  report: Record<string, unknown>;
}

export interface EvaluationMetricDeltaRead {
  metric: string;
  base_value: string | number | null;
  candidate_value: string | number | null;
  delta: string | number | null;
}

export interface EvaluationFindingRead {
  metric: string;
  base_value: string | number | null;
  candidate_value: string | number | null;
  delta: string | number | null;
  reason: string;
}

export interface EvaluationComparisonRead {
  base_evaluation: EvaluationRead;
  candidate_evaluation: EvaluationRead;
  metric_deltas: EvaluationMetricDeltaRead[];
  regressions: EvaluationFindingRead[];
  improvements: EvaluationFindingRead[];
}

