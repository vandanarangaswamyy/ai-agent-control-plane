import { listAgents, listAgentVersions } from "@/lib/api/agents";
import { fetchAllPages } from "@/lib/pagination";
import type { AgentRead, AgentVersionRead } from "@/lib/api/types";

export interface VersionDirectoryEntry {
  agent: AgentRead;
  version: AgentVersionRead;
  label: string;
}

export async function loadAgents(): Promise<AgentRead[]> {
  return fetchAllPages(({ limit, offset }) => listAgents({ limit, offset }));
}

export async function loadAllAgentVersions(): Promise<VersionDirectoryEntry[]> {
  const agents = await loadAgents();
  const versionPages = await Promise.all(
    agents.map(async (agent) => {
      const versions = await fetchAllPages(({ limit, offset }) =>
        listAgentVersions(agent.id, { limit, offset }),
      );
      return versions
        .slice()
        .sort((left, right) => right.version - left.version)
        .map((version) => ({
          agent,
          version,
          label: `${agent.name} v${version.version}${version.name ? ` · ${version.name}` : ""}`,
        }));
    }),
  );

  return versionPages.flat();
}
