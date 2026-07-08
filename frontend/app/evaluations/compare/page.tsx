"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRightLeft, RefreshCw } from "lucide-react";

import { compareEvaluations } from "@/lib/api/evaluations";
import { loadAllAgentVersions } from "@/lib/directory";
import { formatPercent, formatDurationMs, formatCurrency } from "@/lib/format";
import { evaluationResultVariant } from "@/lib/status";
import { PageHeader } from "@/components/page-header";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

export default function EvaluationComparisonPage() {
  const versionsQuery = useQuery({
    queryKey: ["version-directory"],
    queryFn: loadAllAgentVersions,
  });
  const [baseVersionId, setBaseVersionId] = useState("");
  const [candidateVersionId, setCandidateVersionId] = useState("");
  const [suiteName, setSuiteName] = useState("basic-agent-suite");

  useEffect(() => {
    if (versionsQuery.data && versionsQuery.data.length >= 2) {
      setBaseVersionId((current) => current || versionsQuery.data[0].version.id);
      setCandidateVersionId((current) => current || versionsQuery.data[1].version.id);
    }
  }, [versionsQuery.data]);

  const comparisonMutation = useMutation({
    mutationFn: compareEvaluations,
  });

  if (versionsQuery.isLoading) {
    return <LoadingState label="Loading version directory" />;
  }

  if (versionsQuery.isError) {
    return (
      <ErrorState
        message={versionsQuery.error instanceof Error ? versionsQuery.error.message : "Unable to load versions"}
        onRetry={() => void versionsQuery.refetch()}
      />
    );
  }

  const versions = versionsQuery.data ?? [];
  const versionLabelById = new Map(versions.map((entry) => [entry.version.id, entry.label]));
  const comparison = comparisonMutation.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Evaluation Comparison"
        description="Compare agent versions against the same suite and inspect regressions."
        actions={
          <Button variant="outline" onClick={() => void versionsQuery.refetch()}>
            <RefreshCw className="h-4 w-4" />
            Refresh versions
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Comparison inputs</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <label className="space-y-2 text-sm">
            <span className="text-sm font-medium">Base version</span>
            <Select value={baseVersionId} onChange={(event) => setBaseVersionId(event.target.value)}>
              {versions.map((entry) => (
                <option key={entry.version.id} value={entry.version.id}>
                  {entry.label}
                </option>
              ))}
            </Select>
          </label>
          <label className="space-y-2 text-sm">
            <span className="text-sm font-medium">Candidate version</span>
            <Select value={candidateVersionId} onChange={(event) => setCandidateVersionId(event.target.value)}>
              {versions.map((entry) => (
                <option key={entry.version.id} value={entry.version.id}>
                  {entry.label}
                </option>
              ))}
            </Select>
          </label>
          <label className="space-y-2 text-sm">
            <span className="text-sm font-medium">Suite name</span>
            <Input value={suiteName} onChange={(event) => setSuiteName(event.target.value)} />
          </label>
          <div className="md:col-span-3">
            <Button
              onClick={() =>
                void comparisonMutation.mutateAsync({
                  base_agent_version_id: baseVersionId,
                  candidate_agent_version_id: candidateVersionId,
                  suite_name: suiteName,
                })
              }
              disabled={!baseVersionId || !candidateVersionId || !suiteName || comparisonMutation.isPending}
            >
              <ArrowRightLeft className="h-4 w-4" />
              Compare versions
            </Button>
          </div>
        </CardContent>
      </Card>

      {comparisonMutation.isError ? (
        <ErrorState
          message={comparisonMutation.error instanceof Error ? comparisonMutation.error.message : "Comparison failed"}
          onRetry={() =>
            void comparisonMutation.mutateAsync({
              base_agent_version_id: baseVersionId,
              candidate_agent_version_id: candidateVersionId,
              suite_name: suiteName,
            })
          }
        />
      ) : null}

      {!comparison ? (
        <EmptyState
          title="No comparison yet"
          message="Run a comparison to see regression and improvement summaries."
        />
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Base evaluation</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>{versionLabelById.get(comparison.base_evaluation.agent_version_id) ?? comparison.base_evaluation.agent_version_id}</p>
                <p>Status: {comparison.base_evaluation.status}</p>
                <p>Success rate: {formatPercent(comparison.base_evaluation.success_rate)}</p>
                <p>Latency: {formatDurationMs(comparison.base_evaluation.average_latency_ms)}</p>
                <p>Cost: {formatCurrency(comparison.base_evaluation.total_cost)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Candidate evaluation</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>{versionLabelById.get(comparison.candidate_evaluation.agent_version_id) ?? comparison.candidate_evaluation.agent_version_id}</p>
                <p>Status: {comparison.candidate_evaluation.status}</p>
                <p>Success rate: {formatPercent(comparison.candidate_evaluation.success_rate)}</p>
                <p>Latency: {formatDurationMs(comparison.candidate_evaluation.average_latency_ms)}</p>
                <p>Cost: {formatCurrency(comparison.candidate_evaluation.total_cost)}</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Metric deltas</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {comparison.metric_deltas.map((delta) => (
                <div key={delta.metric} className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-3">
                  <span className="font-medium">{delta.metric}</span>
                  <span className="text-sm text-muted-foreground">
                    {String(delta.base_value ?? "—")} → {String(delta.candidate_value ?? "—")} ({String(delta.delta ?? "—")})
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Regressions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {comparison.regressions.length === 0 ? (
                  <EmptyState title="No regressions" message="The candidate did not regress on tracked metrics." />
                ) : (
                  comparison.regressions.map((finding) => (
                    <div key={`${finding.metric}-${finding.reason}`} className="rounded-lg border bg-muted/30 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium">{finding.metric}</span>
                        <Badge variant={evaluationResultVariant("FAILED")}>Regression</Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{finding.reason}</p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Improvements</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {comparison.improvements.length === 0 ? (
                  <EmptyState title="No improvements" message="No positive metric deltas were identified." />
                ) : (
                  comparison.improvements.map((finding) => (
                    <div key={`${finding.metric}-${finding.reason}`} className="rounded-lg border bg-muted/30 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium">{finding.metric}</span>
                        <Badge variant={evaluationResultVariant("PASSED")}>Improvement</Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{finding.reason}</p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
