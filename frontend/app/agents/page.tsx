"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { RefreshCw, Users } from "lucide-react";

import { loadAgents, loadAllAgentVersions } from "@/lib/directory";
import { formatDateTime, formatNumber } from "@/lib/format";
import { lifecycleVariant } from "@/lib/status";
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

export default function AgentsPage() {
  const agentsQuery = useQuery({
    queryKey: ["agents"],
    queryFn: loadAgents,
  });
  const versionsQuery = useQuery({
    queryKey: ["agent-version-directory"],
    queryFn: loadAllAgentVersions,
  });

  if (agentsQuery.isLoading || versionsQuery.isLoading) {
    return <LoadingState label="Loading agent registry" />;
  }

  if (agentsQuery.isError) {
    return (
      <ErrorState
        message={agentsQuery.error instanceof Error ? agentsQuery.error.message : "Unable to load agents"}
        onRetry={() => void agentsQuery.refetch()}
      />
    );
  }

  if (versionsQuery.isError) {
    return (
      <ErrorState
        message={versionsQuery.error instanceof Error ? versionsQuery.error.message : "Unable to load versions"}
        onRetry={() => void versionsQuery.refetch()}
      />
    );
  }

  const agents = agentsQuery.data ?? [];
  const versionDirectory = versionsQuery.data ?? [];

  const groupedVersions = new Map<string, typeof versionDirectory>();
  for (const entry of versionDirectory) {
    const existing = groupedVersions.get(entry.agent.id) ?? [];
    existing.push(entry);
    existing.sort((left, right) => right.version.version - left.version.version);
    groupedVersions.set(entry.agent.id, existing);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Agent Registry"
        description="Registered agents with version history and lifecycle state."
        actions={
          <Button variant="outline" onClick={() => {
            void agentsQuery.refetch();
            void versionsQuery.refetch();
          }}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Agents</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{formatNumber(agents.length)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Versions</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{formatNumber(versionDirectory.length)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Lifecycle coverage</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            DRAFT, EVALUATED, APPROVED, PRODUCTION, and DEPRECATED are all visible in the registry.
          </CardContent>
        </Card>
      </div>

      {agents.length === 0 ? (
        <EmptyState title="No agents yet" message="Agent records will appear here after the backend registry is populated." />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Agents and versions</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Agent</TableHead>
                  <TableHead>Owner</TableHead>
                  <TableHead>Versions</TableHead>
                  <TableHead>Latest activity</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {agents.map((agent) => {
                  const versions = groupedVersions.get(agent.id) ?? [];
                  const latestVersion = versions[0];
                  return (
                    <TableRow key={agent.id}>
                      <TableCell className="font-medium">{agent.name}</TableCell>
                      <TableCell className="text-muted-foreground">{agent.owner ?? "—"}</TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-2">
                          {versions.length > 0 ? (
                            versions.slice(0, 4).map((entry) => (
                              <Badge key={entry.version.id} variant={lifecycleVariant(entry.version.lifecycle)}>
                                v{entry.version.version} {entry.version.lifecycle}
                              </Badge>
                            ))
                          ) : (
                            <span className="text-muted-foreground">No versions</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {latestVersion ? formatDateTime(latestVersion.version.updated_at) : "—"}
                      </TableCell>
                      <TableCell>
                        <Link
                          href={`/agents/${agent.id}`}
                          className="text-sm font-medium text-primary hover:underline"
                        >
                          Open details
                        </Link>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
