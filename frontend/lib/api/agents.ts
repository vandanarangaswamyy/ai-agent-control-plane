import { requestJson } from "@/lib/api/client";
import type { AgentRead, AgentVersionRead, DeploymentEventRead } from "@/lib/api/types";

export interface ListParams {
  limit?: number;
  offset?: number;
}

export async function listAgents(params: ListParams = {}): Promise<AgentRead[]> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) {
    query.set("limit", String(params.limit));
  }
  if (params.offset !== undefined) {
    query.set("offset", String(params.offset));
  }

  return requestJson<AgentRead[]>(
    `/api/v1/agents${query.size > 0 ? `?${query.toString()}` : ""}`,
  );
}

export async function getAgent(agentId: string): Promise<AgentRead> {
  return requestJson<AgentRead>(`/api/v1/agents/${agentId}`);
}

export async function listAgentVersions(
  agentId: string,
  params: ListParams = {},
): Promise<AgentVersionRead[]> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) {
    query.set("limit", String(params.limit));
  }
  if (params.offset !== undefined) {
    query.set("offset", String(params.offset));
  }

  return requestJson<AgentVersionRead[]>(
    `/api/v1/agents/${agentId}/versions${query.size > 0 ? `?${query.toString()}` : ""}`,
  );
}

export async function listAgentDeployments(agentId: string): Promise<DeploymentEventRead[]> {
  return requestJson<DeploymentEventRead[]>(`/api/v1/agents/${agentId}/deployments`);
}

