import { requestJson } from "@/lib/api/client";
import type {
  DeploymentEventRead,
  DeploymentPromotionRead,
  DeploymentRollbackRead,
} from "@/lib/api/types";

export async function promoteDeployment(payload: {
  agent_id: string;
  agent_version_id: string;
  reason?: string | null;
}): Promise<DeploymentPromotionRead> {
  return requestJson<DeploymentPromotionRead>("/api/v1/deployments/promote", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function rollbackDeployment(payload: {
  agent_id: string;
  reason?: string | null;
}): Promise<DeploymentRollbackRead> {
  return requestJson<DeploymentRollbackRead>("/api/v1/deployments/rollback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listAgentDeployments(agentId: string): Promise<DeploymentEventRead[]> {
  return requestJson<DeploymentEventRead[]>(`/api/v1/agents/${agentId}/deployments`);
}

