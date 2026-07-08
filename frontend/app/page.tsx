"use client";

import { BarChart3, Clock3, RefreshCw, ShieldCheck, Users } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { loadDashboardOverview } from "@/lib/api/dashboard";
import { formatDateTime, formatDurationMs, formatNumber, formatPercent } from "@/lib/format";
import { deploymentEventVariant } from "@/lib/status";
import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function DashboardPage() {
  const dashboardQuery = useQuery({
    queryKey: ["dashboard-overview"],
    queryFn: loadDashboardOverview,
  });

  if (dashboardQuery.isLoading) {
    return <LoadingState label="Loading dashboard overview" />;
  }

  if (dashboardQuery.isError) {
    return (
      <ErrorState
        message={dashboardQuery.error instanceof Error ? dashboardQuery.error.message : "Unable to load dashboard"}
        onRetry={() => void dashboardQuery.refetch()}
      />
    );
  }

  const dashboard = dashboardQuery.data;
  if (!dashboard) {
    return <EmptyState title="No dashboard data" message="The backend returned no operational data yet." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard Home"
        description="Operational overview for agents, runtime activity, approvals, and deployments."
        actions={
          <Button variant="outline" onClick={() => void dashboardQuery.refetch()}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        <StatCard label="Total agents" value={formatNumber(dashboard.agentCount)} icon={<Users className="h-4 w-4" />} />
        <StatCard label="Total runs" value={formatNumber(dashboard.totalRuns)} icon={<BarChart3 className="h-4 w-4" />} />
        <StatCard label="Success rate" value={formatPercent(dashboard.successRate)} icon={<ShieldCheck className="h-4 w-4" />} />
        <StatCard label="Failure rate" value={formatPercent(dashboard.failureRate)} icon={<Clock3 className="h-4 w-4" />} />
        <StatCard label="Pending approvals" value={formatNumber(dashboard.pendingApprovals)} icon={<ShieldCheck className="h-4 w-4" />} />
        <StatCard label="Average latency" value={formatDurationMs(dashboard.averageLatencyMs)} icon={<Clock3 className="h-4 w-4" />} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent deployments</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {dashboard.recentDeployments.length === 0 ? (
              <EmptyState
                title="No deployment events"
                message="Deployment history will appear here once versions are promoted or rolled back."
              />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Event</TableHead>
                    <TableHead>Agent</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Target</TableHead>
                    <TableHead>Reason</TableHead>
                    <TableHead>When</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dashboard.recentDeployments.map((deployment) => (
                    <TableRow key={deployment.id}>
                      <TableCell>
                        <Badge variant={deploymentEventVariant(deployment.event_type)}>
                          {deployment.event_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-medium">{deployment.agent_name}</TableCell>
                      <TableCell className="text-muted-foreground">{deployment.source_version_label}</TableCell>
                      <TableCell className="text-muted-foreground">{deployment.target_version_label}</TableCell>
                      <TableCell className="max-w-[18rem] truncate text-muted-foreground">
                        {deployment.reason ?? "—"}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatDateTime(deployment.created_at)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Metric snapshot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 pt-0">
            <div className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-3">
              <span className="text-sm text-muted-foreground">Success rate</span>
              <span className="font-medium">{formatPercent(dashboard.successRate)}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-3">
              <span className="text-sm text-muted-foreground">Failure rate</span>
              <span className="font-medium">{formatPercent(dashboard.failureRate)}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-3">
              <span className="text-sm text-muted-foreground">Average latency</span>
              <span className="font-medium">{formatDurationMs(dashboard.averageLatencyMs)}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-3">
              <span className="text-sm text-muted-foreground">Pending approvals</span>
              <span className="font-medium">{formatNumber(dashboard.pendingApprovals)}</span>
            </div>
            <p className="text-xs text-muted-foreground">
              Total runs and latency are derived from Prometheus metrics. Deployment history is sourced from the backend event log.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
