"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";

import { approveApproval, listApprovals, rejectApproval } from "@/lib/api/approvals";
import { fetchAllPages } from "@/lib/pagination";
import { formatDateTime } from "@/lib/format";
import { approvalStatusVariant, policyDecisionVariant } from "@/lib/status";
import { PageHeader } from "@/components/page-header";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function ApprovalsPage() {
  const queryClient = useQueryClient();
  const approvalsQuery = useQuery({
    queryKey: ["approvals"],
    queryFn: () => fetchAllPages(({ limit, offset }) => listApprovals({ limit, offset })),
  });

  const approveMutation = useMutation({
    mutationFn: (approvalId: string) => approveApproval(approvalId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["approvals"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (approvalId: string) => rejectApproval(approvalId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["approvals"] });
    },
  });

  if (approvalsQuery.isLoading) {
    return <LoadingState label="Loading approval queue" />;
  }

  if (approvalsQuery.isError) {
    return (
      <ErrorState
        message={approvalsQuery.error instanceof Error ? approvalsQuery.error.message : "Unable to load approvals"}
        onRetry={() => void approvalsQuery.refetch()}
      />
    );
  }

  const approvals = approvalsQuery.data ?? [];
  const pendingApprovals = approvals
    .filter((approval) => approval.status === "PENDING")
    .sort((left, right) => right.created_at.localeCompare(left.created_at));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Approval Queue"
        description="Human review queue for policy-gated tool execution."
        actions={
          <Button variant="outline" onClick={() => void approvalsQuery.refetch()}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />

      <Card>
        <CardContent className="flex gap-4 py-4 text-sm text-muted-foreground">
          <span>Pending approvals: {pendingApprovals.length}</span>
          <span>Total reviews: {approvals.length}</span>
        </CardContent>
      </Card>

      {pendingApprovals.length === 0 ? (
        <EmptyState title="No pending approvals" message="Pending items will appear here when tool execution requires review." />
      ) : (
        <Card>
          <CardContent className="pt-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Decision</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Requested</TableHead>
                  <TableHead>Review</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pendingApprovals.map((approval) => (
                  <TableRow key={approval.id}>
                    <TableCell>
                      <Badge variant={approvalStatusVariant(approval.status)}>{approval.status}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={policyDecisionVariant(approval.policy_decision)}>
                        {approval.policy_decision}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[26rem] truncate text-muted-foreground">
                      {approval.reason}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDateTime(approval.created_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          onClick={() => void approveMutation.mutateAsync(approval.id)}
                          disabled={approveMutation.isPending || rejectMutation.isPending}
                        >
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => void rejectMutation.mutateAsync(approval.id)}
                          disabled={approveMutation.isPending || rejectMutation.isPending}
                        >
                          Reject
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
