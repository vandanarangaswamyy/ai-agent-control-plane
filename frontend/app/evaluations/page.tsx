"use client";

import { useQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";

import { listEvaluations } from "@/lib/api/evaluations";
import { formatCurrency, formatDateTime, formatDurationMs, formatPercent, formatNumber } from "@/lib/format";
import { evaluationStatusVariant } from "@/lib/status";
import { fetchAllPages } from "@/lib/pagination";
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

export default function EvaluationsPage() {
  const evaluationsQuery = useQuery({
    queryKey: ["evaluations"],
    queryFn: () => fetchAllPages(({ limit, offset }) => listEvaluations({ limit, offset })),
  });

  if (evaluationsQuery.isLoading) {
    return <LoadingState label="Loading evaluations" />;
  }

  if (evaluationsQuery.isError) {
    return (
      <ErrorState
        message={evaluationsQuery.error instanceof Error ? evaluationsQuery.error.message : "Unable to load evaluations"}
        onRetry={() => void evaluationsQuery.refetch()}
      />
    );
  }

  const evaluations = evaluationsQuery.data ?? [];
  const passed = evaluations.filter((evaluation) => evaluation.status === "PASSED").length;
  const failed = evaluations.filter((evaluation) => evaluation.status === "FAILED").length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Evaluations"
        description="History of suite executions, aggregate metrics, and regression visibility."
        actions={
          <Button variant="outline" onClick={() => void evaluationsQuery.refetch()}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-muted-foreground">Evaluations</p>
            <p className="text-2xl font-semibold">{formatNumber(evaluations.length)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-muted-foreground">Passed</p>
            <p className="text-2xl font-semibold">{formatNumber(passed)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-muted-foreground">Failed</p>
            <p className="text-2xl font-semibold">{formatNumber(failed)}</p>
          </CardContent>
        </Card>
      </div>

      {evaluations.length === 0 ? (
        <EmptyState
          title="No evaluations yet"
          message="Evaluation executions will appear here after suites are run against agent versions."
        />
      ) : (
        <Card>
          <CardContent className="pt-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Suite</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Success</TableHead>
                  <TableHead>Failure</TableHead>
                  <TableHead>Latency</TableHead>
                  <TableHead>Cost</TableHead>
                  <TableHead>Updated</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {evaluations.map((evaluation) => (
                  <TableRow key={evaluation.id}>
                    <TableCell className="font-medium">
                      <div className="flex flex-col">
                        <span>{evaluation.suite_name}</span>
                        <span className="text-xs text-muted-foreground">
                          {evaluation.agent_version_id.slice(0, 8)}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={evaluationStatusVariant(evaluation.status)}>
                        {evaluation.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatPercent(evaluation.success_rate)}</TableCell>
                    <TableCell>{formatPercent(evaluation.failure_rate)}</TableCell>
                    <TableCell>{formatDurationMs(evaluation.average_latency_ms)}</TableCell>
                    <TableCell>{formatCurrency(evaluation.total_cost, 4)}</TableCell>
                    <TableCell className="text-muted-foreground">{formatDateTime(evaluation.updated_at)}</TableCell>
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
