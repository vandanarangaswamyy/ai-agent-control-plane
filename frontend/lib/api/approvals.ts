import { requestJson } from "@/lib/api/client";
import type { ApprovalRequestRead } from "@/lib/api/types";

export interface ListParams {
  limit?: number;
  offset?: number;
}

export async function listApprovals(params: ListParams = {}): Promise<ApprovalRequestRead[]> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) {
    query.set("limit", String(params.limit));
  }
  if (params.offset !== undefined) {
    query.set("offset", String(params.offset));
  }

  return requestJson<ApprovalRequestRead[]>(
    `/api/v1/approvals${query.size > 0 ? `?${query.toString()}` : ""}`,
  );
}

export async function getApproval(approvalId: string): Promise<ApprovalRequestRead> {
  return requestJson<ApprovalRequestRead>(`/api/v1/approvals/${approvalId}`);
}

export async function approveApproval(approvalId: string, reviewedBy = "dashboard"): Promise<ApprovalRequestRead> {
  return requestJson<ApprovalRequestRead>(`/api/v1/approvals/${approvalId}/approve`, {
    method: "POST",
    body: JSON.stringify({ reviewed_by: reviewedBy }),
  });
}

export async function rejectApproval(approvalId: string, reviewedBy = "dashboard"): Promise<ApprovalRequestRead> {
  return requestJson<ApprovalRequestRead>(`/api/v1/approvals/${approvalId}/reject`, {
    method: "POST",
    body: JSON.stringify({ reviewed_by: reviewedBy }),
  });
}
