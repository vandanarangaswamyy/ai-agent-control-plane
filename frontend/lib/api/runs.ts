import { requestJson } from "@/lib/api/client";
import type { RunFailureInspectionRead, RunRead, RunTimelineRead } from "@/lib/api/types";

export interface ListParams {
  limit?: number;
  offset?: number;
}

export async function listRuns(params: ListParams = {}): Promise<RunRead[]> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) {
    query.set("limit", String(params.limit));
  }
  if (params.offset !== undefined) {
    query.set("offset", String(params.offset));
  }

  return requestJson<RunRead[]>(`/api/v1/runs${query.size > 0 ? `?${query.toString()}` : ""}`);
}

export async function getRun(runId: string): Promise<RunRead> {
  return requestJson<RunRead>(`/api/v1/runs/${runId}`);
}

export async function getRunTimeline(runId: string): Promise<RunTimelineRead> {
  return requestJson<RunTimelineRead>(`/api/v1/runs/${runId}/timeline`);
}

export async function getRunFailures(runId: string): Promise<RunFailureInspectionRead> {
  return requestJson<RunFailureInspectionRead>(`/api/v1/runs/${runId}/failures`);
}

