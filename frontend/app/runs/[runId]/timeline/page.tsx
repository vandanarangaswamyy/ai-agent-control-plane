"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";

import { getRunFailures, getRunTimeline } from "@/lib/api/runs";
import { formatDateTime, formatDurationMs, formatNumber } from "@/lib/format";
import {
  traceEventVariant,
  runStatusVariant,
  toolStatusVariant,
  approvalStatusVariant,
  policyDecisionVariant,
} from "@/lib/status";
import type { PolicyDecision } from "@/lib/api/types";
import { PageHeader } from "@/components/page-header";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function RunTimelinePage() {
  const params = useParams<{ runId: string }>();
  const runId = params.runId;

  const timelineQuery = useQuery({
    queryKey: ["run-timeline", runId],
    queryFn: () => getRunTimeline(runId),
  });
  const failureQuery = useQuery({
    queryKey: ["run-failures", runId],
    queryFn: () => getRunFailures(runId),
  });

  if (timelineQuery.isLoading || failureQuery.isLoading) {
    return <LoadingState label="Loading run timeline" />;
  }

  const error = timelineQuery.error ?? failureQuery.error;
  if (error) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : "Unable to load timeline"}
        onRetry={() => {
          void timelineQuery.refetch();
          void failureQuery.refetch();
        }}
      />
    );
  }

  const timeline = timelineQuery.data;
  const failures = failureQuery.data;

  if (!timeline || !failures) {
    return <EmptyState title="Run not found" message="The requested run could not be loaded." />;
  }

  const run = timeline.run;
  const events = [...timeline.events].sort((left, right) => left.timestamp.localeCompare(right.timestamp));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Run Timeline Viewer"
        description={`Run ${run.id.slice(0, 8)} execution timeline and failure analysis.`}
        actions={
          <Button variant="outline" onClick={() => {
            void timelineQuery.refetch();
            void failureQuery.refetch();
          }}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={runStatusVariant(run.status)}>{run.status}</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Latency</CardTitle>
          </CardHeader>
          <CardContent>{formatDurationMs(run.latency_ms)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Start</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">{formatDateTime(run.start_time)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>End</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">{formatDateTime(run.end_time)}</CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Execution timeline</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {events.length === 0 ? (
            <EmptyState
              title="No trace events"
              message="This run does not have persisted trace events yet."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Event</TableHead>
                  <TableHead>Entity</TableHead>
                  <TableHead>Attributes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {events.map((event) => (
                  <TableRow key={event.id}>
                    <TableCell className="text-muted-foreground">{formatDateTime(event.timestamp)}</TableCell>
                    <TableCell>
                      <Badge variant={traceEventVariant(event.event_type)}>{event.name}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {event.entity_type}
                      {event.entity_id ? ` · ${event.entity_id.slice(0, 8)}` : ""}
                    </TableCell>
                    <TableCell className="max-w-[34rem]">
                      <pre className="overflow-x-auto rounded-md bg-muted/50 p-3 text-xs leading-5 text-muted-foreground">
                        {JSON.stringify(event.attributes, null, 2)}
                      </pre>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Failure summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border bg-muted/30 p-4">
              <p className="text-sm font-medium">Runtime error</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {failures.runtime_error_message ?? "No runtime error recorded."}
              </p>
            </div>
            <div className="rounded-lg border bg-muted/30 p-4">
              <p className="text-sm font-medium">Blocked tool calls</p>
              <p className="mt-1 text-sm text-muted-foreground">{formatNumber(failures.blocked_tool_calls.length)}</p>
            </div>
            <div className="rounded-lg border bg-muted/30 p-4">
              <p className="text-sm font-medium">Denied policy checks</p>
              <p className="mt-1 text-sm text-muted-foreground">{formatNumber(failures.denied_policy_checks.length)}</p>
            </div>
            <div className="rounded-lg border bg-muted/30 p-4">
              <p className="text-sm font-medium">Approval failures</p>
              <p className="mt-1 text-sm text-muted-foreground">{formatNumber(failures.approval_failures.length)}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Failure details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="mb-2 text-sm font-medium">Failed tool calls</p>
              {failures.failed_tool_calls.length === 0 ? (
                <p className="text-sm text-muted-foreground">None</p>
              ) : (
                <div className="space-y-2">
                  {failures.failed_tool_calls.map((call) => (
                    <div key={call.id} className="rounded-lg border bg-muted/30 p-3 text-sm">
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium">{call.tool_name}</span>
                        <Badge variant={toolStatusVariant(call.status)}>{call.status}</Badge>
                      </div>
                      <p className="mt-1 text-muted-foreground">{call.error_message ?? "No error message"}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <p className="mb-2 text-sm font-medium">Denied policy checks</p>
              {failures.denied_policy_checks.length === 0 ? (
                <p className="text-sm text-muted-foreground">None</p>
              ) : (
                <div className="space-y-2">
                  {failures.denied_policy_checks.map((event) => (
                    <div key={event.id} className="rounded-lg border bg-muted/30 p-3 text-sm">
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium">{event.name}</span>
                        <Badge
                          variant={policyDecisionVariant(
                            String(event.attributes.policy_decision ?? "DENY").toUpperCase() as PolicyDecision,
                          )}
                        >
                          {String(event.attributes.policy_decision ?? "DENY")}
                        </Badge>
                      </div>
                      <p className="mt-1 text-muted-foreground">{String(event.attributes.reason ?? "No reason provided")}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <p className="mb-2 text-sm font-medium">Approval failures</p>
              {failures.approval_failures.length === 0 ? (
                <p className="text-sm text-muted-foreground">None</p>
              ) : (
                <div className="space-y-2">
                  {failures.approval_failures.map((approval) => (
                    <div key={approval.id} className="rounded-lg border bg-muted/30 p-3 text-sm">
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium">{approval.reason}</span>
                        <Badge variant={approvalStatusVariant(approval.status)}>{approval.status}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
