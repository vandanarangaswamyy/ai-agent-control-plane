import { requestJson } from "@/lib/api/client";
import type {
  EvaluationComparisonRead,
  EvaluationRead,
  EvaluationReportRead,
} from "@/lib/api/types";

export interface ListParams {
  limit?: number;
  offset?: number;
}

export async function listEvaluations(params: ListParams = {}): Promise<EvaluationRead[]> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) {
    query.set("limit", String(params.limit));
  }
  if (params.offset !== undefined) {
    query.set("offset", String(params.offset));
  }

  return requestJson<EvaluationRead[]>(
    `/api/v1/evaluations${query.size > 0 ? `?${query.toString()}` : ""}`,
  );
}

export async function getEvaluation(evaluationId: string): Promise<EvaluationRead> {
  return requestJson<EvaluationRead>(`/api/v1/evaluations/${evaluationId}`);
}

export async function getEvaluationReport(evaluationId: string): Promise<EvaluationReportRead> {
  return requestJson<EvaluationReportRead>(`/api/v1/evaluations/${evaluationId}/report`);
}

export interface CompareRequest {
  base_agent_version_id: string;
  candidate_agent_version_id: string;
  suite_name: string;
}

export async function compareEvaluations(
  payload: CompareRequest,
): Promise<EvaluationComparisonRead> {
  return requestJson<EvaluationComparisonRead>("/api/v1/evaluations/compare", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

