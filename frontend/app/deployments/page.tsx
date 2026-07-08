"use client";

import { useQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";

import { listAgentDeployments } from "@/lib/api/agents";
import { loadAgents, loadAllAgentVersions } from "@/lib/directory";
import { formatDateTime } from "@/lib/format";
import { deploymentEventVariant } from "@/lib/status";
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

export default function DeploymentsPage() {
  const deploymentsQuery = useQuery({
    queryKey: ["deployment-history"],
    queryFn: async () => {
      const [agents, versions] = await Promise.all([loadAgents(), loadAllAgentVersions()]);
      const versionLabelMap = new Map(versions.map((entry) => [entry.version.id, entry.label]));
      const deploymentGroups = await Promise.all(
        agents.map(async (agent) => {
          const events = await listAgentDeployments(agent.id);
          return events.map((event) => ({
            ...event,
            agent_name: agent.name,
            source_version_label:
              (event.source_version_id && versionLabelMap.get(event.source_version_id)) ??
              event.source_version_id ??
              "—",
            target_version_label:
              (event.target_version_id && versionLabelMap.get(event.target_version_id)) ??
              event.target_version_id ??
              "—",
          }));
        }),
      );

      return deploymentGroups
        .flat()
        .sort((left, right) => right.created_at.localeCompare(left.created_at));
    },
  });

  if (deploymentsQuery.isLoading) {
    return <LoadingState label="Loading deployment history" />;
  }

  if (deploymentsQuery.isError) {
    return (
      <ErrorState
        message={deploymentsQuery.error instanceof Error ? deploymentsQuery.error.message : "Unable to load deployment history"}
        onRetry={() => void deploymentsQuery.refetch()}
      />
    );
  }

  const deployments = deploymentsQuery.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Deployment History"
        description="Promotion and rollback events across agents and versions."
        actions={
          <Button variant="outline" onClick={() => void deploymentsQuery.refetch()}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />

      <Card>
        <CardContent className="py-4 text-sm text-muted-foreground">
          Deployment events are ordered from newest to oldest and include source and target versions.
        </CardContent>
      </Card>

      {deployments.length === 0 ? (
        <EmptyState
          title="No deployment events"
          message="Promotion and rollback history will appear here once deployment control is exercised."
        />
      ) : (
        <Card>
          <CardContent className="pt-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Event</TableHead>
                  <TableHead>Agent</TableHead>
                  <TableHead>Source version</TableHead>
                  <TableHead>Target version</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>When</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {deployments.map((deployment) => (
                  <TableRow key={deployment.id}>
                    <TableCell>
                      <Badge variant={deploymentEventVariant(deployment.event_type)}>
                        {deployment.event_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-medium">{deployment.agent_name}</TableCell>
                    <TableCell className="text-muted-foreground">{deployment.source_version_label}</TableCell>
                    <TableCell className="text-muted-foreground">{deployment.target_version_label}</TableCell>
                    <TableCell className="max-w-[22rem] truncate text-muted-foreground">
                      {deployment.reason ?? "—"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatDateTime(deployment.created_at)}</TableCell>
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
