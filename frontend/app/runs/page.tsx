"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";

import { listRuns } from "@/lib/api/runs";
import { fetchAllPages } from "@/lib/pagination";
import { formatCurrency, formatDateTime, formatDurationMs, formatNumber } from "@/lib/format";
import { runStatusVariant } from "@/lib/status";
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

export default function RunsPage() {
  const runsQuery = useQuery({
    queryKey: ["runs"],
    queryFn: () => fetchAllPages(({ limit, offset }) => listRuns({ limit, offset })),
  });

  if (runsQuery.isLoading) {
    return <LoadingState label="Loading run history" />;
  }

  if (runsQuery.isError) {
    return (
      <ErrorState
        message={runsQuery.error instanceof Error ? runsQuery.error.message : "Unable to load runs"}
        onRetry={() => void runsQuery.refetch()}
      />
    );
  }

  const runs = runsQuery.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Run History"
        description="Execution records, statuses, latency, and cost."
        actions={
          <Button variant="outline" onClick={() => void runsQuery.refetch()}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />

      <Card>
        <CardContent className="flex gap-4 py-4 text-sm text-muted-foreground">
          <span>Total runs: {formatNumber(runs.length)}</span>
        </CardContent>
      </Card>

      {runs.length === 0 ? (
        <EmptyState title="No runs yet" message="Agent run records will appear here after execution." />
      ) : (
        <Card>
          <CardContent className="pt-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Run</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Finished</TableHead>
                  <TableHead>Latency</TableHead>
                  <TableHead>Cost</TableHead>
                  <TableHead>Timeline</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell>
                      <Badge variant={runStatusVariant(run.status)}>{run.status}</Badge>
                    </TableCell>
                    <TableCell className="font-medium">
                      <div className="flex flex-col">
                        <span>{run.id.slice(0, 8)}</span>
                        <span className="text-xs text-muted-foreground">{run.agent_version_id.slice(0, 8)}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatDateTime(run.start_time)}</TableCell>
                    <TableCell className="text-muted-foreground">{formatDateTime(run.end_time)}</TableCell>
                    <TableCell className="text-muted-foreground">{formatDurationMs(run.latency_ms)}</TableCell>
                    <TableCell className="text-muted-foreground">{formatCurrency(run.estimated_cost)}</TableCell>
                    <TableCell>
                      <Link
                        href={`/runs/${run.id}/timeline`}
                        className="text-sm font-medium text-primary hover:underline"
                      >
                        View timeline
                      </Link>
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
