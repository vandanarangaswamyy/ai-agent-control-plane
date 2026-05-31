# API Reference

All public routes are served under the FastAPI application. Versioned product APIs live under `/api/v1`.

Standard error format:

```json
{
  "error": {
    "type": "BusinessRuleViolationError",
    "message": "latest evaluation is required before promotion"
  }
}
```

## Health and Metrics

### `GET /health`

Returns process health.

Example response:

```json
{
  "status": "ok",
  "service": "AI Agent Control Plane",
  "environment": "local"
}
```

### `GET /ready`

Returns readiness state for dependency checks.

Example response:

```json
{
  "status": "ready",
  "checks": [
    {
      "name": "database",
      "status": "ready",
      "message": null
    }
  ]
}
```

### `GET /metrics`

Returns Prometheus-formatted metrics text.

Example response:

```text
# HELP agent_runs_total Total agent runs
# TYPE agent_runs_total counter
agent_runs_total 12
```

## Agents

### `POST /api/v1/agents`

Create an agent.

Request:

```json
{
  "name": "research-agent",
  "description": "Summarizes uploaded material",
  "owner": "platform"
}
```

Response:

```json
{
  "id": "8c8e9f6d-9a72-4d5c-8b9c-5b2b8840a5c3",
  "name": "research-agent",
  "description": "Summarizes uploaded material",
  "owner": "platform",
  "created_at": "2026-05-31T10:00:00Z",
  "updated_at": "2026-05-31T10:00:00Z"
}
```

### `GET /api/v1/agents`

List agents.

### `GET /api/v1/agents/{agent_id}`

Get a single agent.

### `POST /api/v1/agents/{agent_id}/versions`

Create a new agent version.

Request:

```json
{
  "name": "v1",
  "prompt": "Use the browser tool to summarize the page",
  "model": "claude-sonnet-4",
  "tool_config": {
    "default_tool": "browser"
  },
  "runtime_config": {
    "temperature": 0
  }
}
```

### `GET /api/v1/agents/{agent_id}/versions`

List versions for an agent.

### `PATCH /api/v1/agents/{agent_id}/versions/{version_id}`

Update draft version metadata.

### `POST /api/v1/agents/{agent_id}/versions/{version_id}/deprecate`

Deprecate a version.

### `GET /api/v1/agents/{agent_id}/deployments`

Return ordered deployment history for the agent.

## Runs

### `POST /api/v1/runs`

Create and execute a run.

Request:

```json
{
  "agent_version_id": "b4b6d5ad-61ce-42b9-9a61-4100dd771516",
  "task": "Read a document and summarize it"
}
```

Example response:

```json
{
  "id": "f0e5d3e2-4b1d-4a88-a4d4-5f4a7f0b4c6e",
  "status": "SUCCESS",
  "start_time": "2026-05-31T10:05:00Z",
  "end_time": "2026-05-31T10:05:01Z",
  "latency_ms": 1000,
  "output": {
    "task": "Read a document and summarize it",
    "tool": "browser",
    "tool_output": {
      "summary": "Mock browser result for: Read a document and summarize it"
    }
  },
  "token_count": 8,
  "estimated_cost": "0.000100"
}
```

### `GET /api/v1/runs`

List runs.

### `GET /api/v1/runs/{run_id}`

Get a single run.

### `GET /api/v1/runs/{run_id}/timeline`

Return a chronological execution timeline for the run.

### `GET /api/v1/runs/{run_id}/failures`

Return structured failure analysis for the run.

## Traces

### `GET /api/v1/traces/{trace_id}`

Return all persisted events for a trace ID.

## Approvals

### `GET /api/v1/approvals`

List approval requests.

### `GET /api/v1/approvals/{approval_id}`

Get a single approval request.

### `POST /api/v1/approvals/{approval_id}/approve`

Approve a blocked action.

Request:

```json
{
  "reviewed_by": "ops@example.com"
}
```

### `POST /api/v1/approvals/{approval_id}/reject`

Reject a blocked action.

Request:

```json
{
  "reviewed_by": "ops@example.com"
}
```

## Evaluations

### `POST /api/v1/evaluations`

Run an evaluation suite against an agent version.

Request:

```json
{
  "agent_version_id": "b4b6d5ad-61ce-42b9-9a61-4100dd771516",
  "suite_name": "basic-agent-suite"
}
```

### `GET /api/v1/evaluations`

List evaluations.

### `GET /api/v1/evaluations/{evaluation_id}`

Get an evaluation summary.

### `GET /api/v1/evaluations/{evaluation_id}/report`

Get the full evaluation report.

### `POST /api/v1/evaluations/compare`

Compare two agent versions.

Request:

```json
{
  "base_agent_version_id": "11111111-1111-1111-1111-111111111111",
  "candidate_agent_version_id": "22222222-2222-2222-2222-222222222222",
  "suite_name": "basic-agent-suite"
}
```

Example response:

```json
{
  "metric_deltas": [
    {
      "metric": "success_rate",
      "base_value": "1.000000",
      "candidate_value": "0.500000",
      "delta": "-0.500000"
    }
  ],
  "regressions": [
    {
      "metric": "success_rate",
      "base_value": "1.000000",
      "candidate_value": "0.500000",
      "delta": "-0.500000",
      "reason": "success_rate decreased"
    }
  ],
  "improvements": []
}
```

## Deployments

### `POST /api/v1/deployments/promote`

Promote an agent version to production.

Request:

```json
{
  "agent_id": "8c8e9f6d-9a72-4d5c-8b9c-5b2b8840a5c3",
  "agent_version_id": "b4b6d5ad-61ce-42b9-9a61-4100dd771516",
  "reason": "latest evaluation passed and exceeded threshold"
}
```

### `POST /api/v1/deployments/rollback`

Rollback production to the previous production-capable version.

Request:

```json
{
  "agent_id": "8c8e9f6d-9a72-4d5c-8b9c-5b2b8840a5c3",
  "reason": "regression detected in production"
}
```

## Common Error Examples

### Not found

```json
{
  "error": {
    "type": "NotFoundError",
    "message": "agent not found"
  }
}
```

### Validation error

```json
{
  "detail": [
    {
      "type": "uuid_parsing",
      "loc": ["body", "agent_version_id"],
      "msg": "Input should be a valid UUID",
      "input": "not-a-uuid"
    }
  ]
}
```

### Business rule violation

```json
{
  "error": {
    "type": "BusinessRuleViolationError",
    "message": "latest evaluation must pass before promotion"
  }
}
```
