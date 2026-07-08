import { listAgentDeployments } from "@/lib/api/agents";
import { listApprovals } from "@/lib/api/approvals";
import { getMetricsText, } from "@/lib/api/metrics";
import { loadAgents, loadAllAgentVersions } from "@/lib/directory";
import { parsePrometheusMetrics, averageFromHistogram } from "@/lib/metrics";
import type { DeploymentEventRead, ApprovalRequestRead } from "@/lib/api/types";

export interface DashboardOverview {
  agentCount: number;
  totalRuns: number;
  successRate: number | null;
  failureRate: number | null;
  pendingApprovals: number;
  averageLatencyMs: number | null;
  recentDeployments: Array<
    DeploymentEventRead & {
      agent_name: string;
      source_version_label: string;
      target_version_label: string;
    }
  >;
}

async function listAllApprovals(): Promise<ApprovalRequestRead[]> {
  const approvals: ApprovalRequestRead[] = [];
  const pageSize = 100;
  let offset = 0;

  for (;;) {
    const page = await listApprovals({ limit: pageSize, offset });
    approvals.push(...page);
    if (page.length < pageSize) {
      break;
    }
    offset += pageSize;
  }

  return approvals;
}

export async function loadDashboardOverview(): Promise<DashboardOverview> {
  const agents = await loadAgents();
  const versions = await loadAllAgentVersions();
  const approvals = await listAllApprovals();
  const metricsText = await getMetricsText();
  const metrics = parsePrometheusMetrics(metricsText);
  const averageLatencySeconds = averageFromHistogram(metrics, "agent_run_latency_seconds");
  const versionLabelMap = new Map(versions.map((entry) => [entry.version.id, entry.label]));

  const deploymentPairs = await Promise.all(
    agents.map(async (agent) => {
      const deployments = await listAgentDeployments(agent.id);
      return deployments.map((deployment) => ({
        ...deployment,
        agent_name: agent.name,
        source_version_label:
          (deployment.source_version_id && versionLabelMap.get(deployment.source_version_id)) ??
          deployment.source_version_id ??
          "—",
        target_version_label:
          (deployment.target_version_id && versionLabelMap.get(deployment.target_version_id)) ??
          deployment.target_version_id ??
          "—",
      }));
    }),
  );

  const recentDeployments = deploymentPairs
    .flat()
    .sort((left, right) => right.created_at.localeCompare(left.created_at))
    .slice(0, 12);

  const totalRuns =
    metrics.counters.agent_runs_total ??
    metrics.counters.agent_runs ??
    0;
  const successfulRuns = metrics.counters.agent_runs_success_total ?? metrics.counters.agent_runs_success ?? 0;
  const failedRuns = metrics.counters.agent_runs_failed_total ?? metrics.counters.agent_runs_failed ?? 0;

  return {
    agentCount: agents.length,
    totalRuns,
    successRate: totalRuns > 0 ? (successfulRuns / totalRuns) * 100 : null,
    failureRate: totalRuns > 0 ? (failedRuns / totalRuns) * 100 : null,
    pendingApprovals: approvals.filter((approval) => approval.status === "PENDING").length,
    averageLatencyMs: averageLatencySeconds === null ? null : averageLatencySeconds * 1000,
    recentDeployments,
  };
}
