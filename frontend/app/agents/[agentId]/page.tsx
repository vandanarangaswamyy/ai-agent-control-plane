"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { GitBranch, RefreshCw, Sparkles, BarChart3 } from "lucide-react";

import { getAgent, listAgentDeployments, listAgentVersions } from "@/lib/api/agents";
import { listEvaluations } from "@/lib/api/evaluations";
import { formatDateTime, formatDurationMs, formatNumber, formatPercent } from "@/lib/format";
import { lifecycleVariant, deploymentEventVariant, evaluationStatusVariant } from "@/lib/status";
import { PageHeader } from "@/components/page-header";
import { ErrorState } from "@/components/error-state";
import { EmptyState } from "@/components/empty-state";
import { LoadingState } from "@/components/loading-state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { fetchAllPages } from "@/lib/pagination";

export default function AgentDetailsPage() {
  const params = useParams<{ agentId: string }>();
  const agentId = params.agentId;
  const [tab, setTab] = useState("versions");

  const agentQuery = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => getAgent(agentId),
  });
  const versionsQuery = useQuery({
    queryKey: ["agent-versions", agentId],
    queryFn: () => fetchAllPages(({ limit, offset }) => listAgentVersions(agentId, { limit, offset })),
  });
  const deploymentsQuery = useQuery({
    queryKey: ["agent-deployments", agentId],
    queryFn: () => listAgentDeployments(agentId),
  });
  const evaluationsQuery = useQuery({
    queryKey: ["agent-evaluations", agentId],
    queryFn: async () => {
      const [versions, evaluations] = await Promise.all([
        fetchAllPages(({ limit, offset }) => listAgentVersions(agentId, { limit, offset })),
        fetchAllPages(({ limit, offset }) => listEvaluations({ limit, offset })),
      ]);
      const versionIds = new Set(versions.map((version) => version.id));
      return evaluations.filter((evaluation) => versionIds.has(evaluation.agent_version_id));
    },
  });

  if (agentQuery.isLoading || versionsQuery.isLoading || deploymentsQuery.isLoading || evaluationsQuery.isLoading) {
    return <LoadingState label="Loading agent details" />;
  }

  const error =
    agentQuery.error ?? versionsQuery.error ?? deploymentsQuery.error ?? evaluationsQuery.error;
  if (error) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : "Unable to load agent details"}
        onRetry={() => {
          void agentQuery.refetch();
          void versionsQuery.refetch();
          void deploymentsQuery.refetch();
          void evaluationsQuery.refetch();
        }}
      />
    );
  }

  const agent = agentQuery.data;
  const versions = versionsQuery.data ?? [];
  const deployments = deploymentsQuery.data ?? [];
  const evaluations = evaluationsQuery.data ?? [];

  if (!agent) {
    return <EmptyState title="Agent not found" message="The requested agent record could not be loaded." />;
  }

  const productionVersion = versions.find((version) => version.lifecycle === "PRODUCTION");
  const latestDeployments = [...deployments].sort((left, right) => right.created_at.localeCompare(left.created_at));
  const latestVersions = [...versions].sort((left, right) => right.version - left.version);
  const latestEvaluations = [...evaluations].sort((left, right) => right.updated_at.localeCompare(left.updated_at));

  return (
    <div className="space-y-6">
      <PageHeader
        title={agent.name}
        description={agent.description ?? "No agent description provided."}
        actions={
          <Button variant="outline" onClick={() => {
            void agentQuery.refetch();
            void versionsQuery.refetch();
            void deploymentsQuery.refetch();
            void evaluationsQuery.refetch();
          }}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Version count</CardTitle>
          </CardHeader>
              <CardContent className="text-2xl font-semibold">{formatNumber(versions.length)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Deployments</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{formatNumber(deployments.length)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Evaluations</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{formatNumber(evaluations.length)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Production</CardTitle>
          </CardHeader>
          <CardContent>
            {productionVersion ? (
              <Badge variant={lifecycleVariant(productionVersion.lifecycle)}>
                v{productionVersion.version} {productionVersion.lifecycle}
              </Badge>
            ) : (
              <span className="text-sm text-muted-foreground">No production version</span>
            )}
          </CardContent>
        </Card>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="versions">
            <Sparkles className="mr-2 h-4 w-4" />
            Versions
          </TabsTrigger>
          <TabsTrigger value="deployments">
            <GitBranch className="mr-2 h-4 w-4" />
            Deployments
          </TabsTrigger>
          <TabsTrigger value="evaluations">
            <BarChart3 className="mr-2 h-4 w-4" />
            Evaluations
          </TabsTrigger>
        </TabsList>

        <TabsContent value="versions">
          <Card>
            <CardHeader>
              <CardTitle>Version history</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {latestVersions.length === 0 ? (
                <EmptyState
                  title="No versions"
                  message="Create agent versions in the backend to see them here."
                />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Version</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Model</TableHead>
                      <TableHead>Lifecycle</TableHead>
                      <TableHead>Updated</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {latestVersions.map((version) => (
                      <TableRow key={version.id}>
                        <TableCell className="font-medium">v{version.version}</TableCell>
                        <TableCell className="text-muted-foreground">{version.name ?? "—"}</TableCell>
                        <TableCell className="text-muted-foreground">{version.model}</TableCell>
                        <TableCell>
                          <Badge variant={lifecycleVariant(version.lifecycle)}>{version.lifecycle}</Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {formatDateTime(version.updated_at)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="deployments">
          <Card>
            <CardHeader>
              <CardTitle>Deployment state</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {latestDeployments.length === 0 ? (
                <EmptyState
                  title="No deployment history"
                  message="Promotions and rollbacks for this agent will appear here."
                />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Event</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead>Target</TableHead>
                      <TableHead>Reason</TableHead>
                      <TableHead>When</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {latestDeployments.map((deployment) => (
                      <TableRow key={deployment.id}>
                        <TableCell>
                          <Badge variant={deploymentEventVariant(deployment.event_type)}>
                            {deployment.event_type}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {deployment.source_version_id ?? "—"}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {deployment.target_version_id ?? "—"}
                        </TableCell>
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
        </TabsContent>

        <TabsContent value="evaluations">
          <Card>
            <CardHeader>
              <CardTitle>Evaluation history</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {latestEvaluations.length === 0 ? (
                <EmptyState
                  title="No evaluations"
                  message="Run an evaluation suite against a version to see results here."
                />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Suite</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Success</TableHead>
                      <TableHead>Failure</TableHead>
                      <TableHead>Latency</TableHead>
                      <TableHead>Updated</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {latestEvaluations.map((evaluation) => (
                      <TableRow key={evaluation.id}>
                        <TableCell className="font-medium">{evaluation.suite_name}</TableCell>
                        <TableCell>
                          <Badge variant={evaluationStatusVariant(evaluation.status)}>
                            {evaluation.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{formatPercent(evaluation.success_rate)}</TableCell>
                        <TableCell>{formatPercent(evaluation.failure_rate)}</TableCell>
                        <TableCell>{formatDurationMs(evaluation.average_latency_ms)}</TableCell>
                        <TableCell className="text-muted-foreground">
                          {formatDateTime(evaluation.updated_at)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
