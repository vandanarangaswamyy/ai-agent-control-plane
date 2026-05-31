# AI Agent Control Plane Implementation Roadmap

## Source Specification

This roadmap is based on `AI_Agent_Control_Plane_Codex_Spec.docx`, which defines a production-grade AI AgentOps control plane for deploying, evaluating, monitoring, and safely operating AI agents. The platform is infrastructure for agent lifecycle management, not a chatbot.

Core problem areas:

- Agent versioning
- Evaluation infrastructure
- Tool-call observability
- Safety guardrails and approvals
- Deployment controls
- Regression detection
- Rollback mechanisms

Primary backend stack:

- Python 3.12+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Celery
- Redis
- Pytest
- OpenTelemetry
- Prometheus/Grafana

Frontend and Terraform are intentionally deferred until the backend MVP is complete.

## Delivery Principles

1. Build backend contracts before UI.
2. Treat every agent execution as auditable operational data.
3. Keep execution, safety, evaluation, and deployment as separate service boundaries.
4. Use clean architecture with dependency injection, service layer, repository pattern, and explicit domain models.
5. Keep external-risk tools mocked or sandboxed for MVP.
6. Make observability a first-class implementation requirement, not a final add-on.
7. Do not implement frontend or Terraform until the backend MVP has stable APIs, migrations, tests, and seed data.

## Milestone 0: Repository Structure, Architecture, Schema, and Local Docker

Goal: create the foundation before implementing product behavior.

### Repository Structure

Recommended monorepo layout:

```text
.
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── agents.py
│   │   │       ├── approvals.py
│   │   │       ├── deployments.py
│   │   │       ├── evaluations.py
│   │   │       ├── runs.py
│   │   │       └── traces.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   ├── security.py
│   │   │   └── telemetry.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── models/
│   │   │       ├── agent.py
│   │   │       ├── approval.py
│   │   │       ├── deployment.py
│   │   │       ├── evaluation.py
│   │   │       ├── run.py
│   │   │       ├── tool_call.py
│   │   │       └── trace.py
│   │   ├── domain/
│   │   │   ├── enums.py
│   │   │   ├── errors.py
│   │   │   └── value_objects.py
│   │   ├── repositories/
│   │   │   ├── agents.py
│   │   │   ├── approvals.py
│   │   │   ├── deployments.py
│   │   │   ├── evaluations.py
│   │   │   ├── runs.py
│   │   │   └── traces.py
│   │   ├── schemas/
│   │   │   ├── agents.py
│   │   │   ├── approvals.py
│   │   │   ├── deployments.py
│   │   │   ├── evaluations.py
│   │   │   ├── runs.py
│   │   │   └── traces.py
│   │   ├── services/
│   │   │   ├── agent_registry.py
│   │   │   ├── deployment_control.py
│   │   │   ├── evaluation_harness.py
│   │   │   ├── runtime.py
│   │   │   ├── safety_gateway.py
│   │   │   └── trace_service.py
│   │   ├── tools/
│   │   │   ├── base.py
│   │   │   ├── browser.py
│   │   │   ├── email.py
│   │   │   ├── file.py
│   │   │   └── terminal.py
│   │   ├── workers/
│   │   │   ├── celery_app.py
│   │   │   └── tasks.py
│   │   └── main.py
│   ├── tests/
│   │   ├── api/
│   │   ├── integration/
│   │   ├── services/
│   │   └── unit/
│   ├── pyproject.toml
│   ├── alembic.ini
│   └── Dockerfile
├── docker/
│   ├── grafana/
│   │   └── provisioning/
│   └── prometheus/
│       └── prometheus.yml
├── docs/
│   ├── implementation-roadmap.md
│   └── architecture.md
├── evals/
│   ├── suites/
│   └── fixtures/
├── scripts/
│   ├── migrate.sh
│   ├── seed.sh
│   └── test.sh
├── docker-compose.yml
├── docker-compose.observability.yml
├── .env.example
├── README.md
└── Makefile
```

Deferred until backend MVP completion:

```text
frontend/
infra/
```

### Architecture Decisions

Backend architecture:

- FastAPI exposes versioned REST APIs under `/api/v1`.
- SQLAlchemy ORM models map to PostgreSQL tables.
- Alembic owns all schema migrations.
- Repositories isolate database persistence from services.
- Services own business behavior and transaction boundaries.
- Pydantic schemas define request and response contracts.
- Celery workers execute long-running agent runs and evaluations.
- Redis backs Celery broker/result state for local development.
- OpenTelemetry spans are emitted from API handlers, services, tool calls, policy checks, and worker tasks.

Primary bounded contexts:

- Agent Registry: agents, versions, lifecycle metadata.
- Runtime: agent runs, execution state, tool invocation orchestration.
- Tool Framework: FileTool, BrowserTool mock, EmailTool mock, TerminalTool sandboxed mock.
- Safety Gateway: policy checks, decisions, approval queue.
- Evaluation Harness: suites, results, regression comparison.
- Trace Service: execution timelines, trace lookup, failure inspection.
- Deployment Control: promotion, rollback, deployment events.

Important service rules:

- Runtime cannot invoke a tool directly without a Safety Gateway policy check.
- Every tool invocation creates a `tool_calls` row and a trace event.
- Any `REQUIRE_APPROVAL` policy decision pauses or blocks execution and creates an approval request.
- Deployment promotion cannot bypass evaluation gate checks.
- Rollback is represented as a deployment event, not as mutation without history.

### Domain Enums

Initial enum set:

- `AgentRunStatus`: `PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `BLOCKED`
- `AgentVersionLifecycle`: `DRAFT`, `EVALUATED`, `APPROVED`, `PRODUCTION`, `DEPRECATED`
- `PolicyDecision`: `ALLOW`, `REQUIRE_APPROVAL`, `DENY`
- `ApprovalStatus`: `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`
- `ToolCallStatus`: `PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `BLOCKED`, `DENIED`
- `EvaluationStatus`: `PENDING`, `RUNNING`, `PASSED`, `FAILED`
- `DeploymentEventType`: `PROMOTE`, `ROLLBACK`, `DEPRECATE`
- `TraceEventType`: `AGENT_RUN`, `LLM_CALL`, `TOOL_CALL`, `POLICY_CHECK`, `EVALUATION`

### Database Schema

Use UUID primary keys for operational entities and timezone-aware timestamps for all time fields.

#### `agents`

- `id` UUID primary key
- `name` text, unique, required
- `description` text nullable
- `owner` text nullable
- `created_at` timestamptz required
- `updated_at` timestamptz required

Indexes:

- unique index on `name`

#### `agent_versions`

- `id` UUID primary key
- `agent_id` UUID foreign key to `agents.id`
- `version` integer required
- `name` text nullable
- `prompt` text required
- `model` text required
- `tool_config` jsonb required default `{}`
- `runtime_config` jsonb required default `{}`
- `lifecycle` enum required default `DRAFT`
- `created_at` timestamptz required
- `updated_at` timestamptz required

Indexes:

- unique index on `(agent_id, version)`
- index on `(agent_id, lifecycle)`

#### `agent_runs`

- `id` UUID primary key
- `agent_id` UUID foreign key to `agents.id`
- `agent_version_id` UUID foreign key to `agent_versions.id`
- `status` enum required default `PENDING`
- `input` jsonb required default `{}`
- `output` jsonb nullable
- `error_message` text nullable
- `start_time` timestamptz nullable
- `end_time` timestamptz nullable
- `latency_ms` integer nullable
- `token_count` integer nullable
- `estimated_cost` numeric nullable
- `trace_id` text nullable
- `created_at` timestamptz required
- `updated_at` timestamptz required

Indexes:

- index on `(agent_id, created_at)`
- index on `(agent_version_id, created_at)`
- index on `(status, created_at)`
- index on `trace_id`

#### `tool_calls`

- `id` UUID primary key
- `agent_run_id` UUID foreign key to `agent_runs.id`
- `tool_name` text required
- `status` enum required
- `input` jsonb required default `{}`
- `output` jsonb nullable
- `error_message` text nullable
- `policy_decision` enum nullable
- `approval_request_id` UUID nullable foreign key to `approval_requests.id`
- `start_time` timestamptz nullable
- `end_time` timestamptz nullable
- `latency_ms` integer nullable
- `trace_id` text nullable
- `span_id` text nullable
- `created_at` timestamptz required
- `updated_at` timestamptz required

Indexes:

- index on `(agent_run_id, created_at)`
- index on `(tool_name, created_at)`
- index on `(status, created_at)`

#### `traces`

- `id` UUID primary key
- `trace_id` text required
- `span_id` text nullable
- `parent_span_id` text nullable
- `event_type` enum required
- `entity_type` text required
- `entity_id` UUID nullable
- `name` text required
- `attributes` jsonb required default `{}`
- `timestamp` timestamptz required

Indexes:

- index on `trace_id`
- index on `(event_type, timestamp)`
- index on `(entity_type, entity_id)`

#### `evaluations`

- `id` UUID primary key
- `agent_id` UUID foreign key to `agents.id`
- `agent_version_id` UUID foreign key to `agent_versions.id`
- `name` text required
- `suite_name` text required
- `status` enum required default `PENDING`
- `baseline_agent_version_id` UUID nullable foreign key to `agent_versions.id`
- `started_at` timestamptz nullable
- `completed_at` timestamptz nullable
- `created_at` timestamptz required
- `updated_at` timestamptz required

Indexes:

- index on `(agent_version_id, created_at)`
- index on `(status, created_at)`

#### `evaluation_results`

- `id` UUID primary key
- `evaluation_id` UUID foreign key to `evaluations.id`
- `case_name` text required
- `success` boolean required
- `metrics` jsonb required default `{}`
- `failure_reason` text nullable
- `created_at` timestamptz required

Required metrics keys:

- `success_rate`
- `tool_accuracy`
- `latency`
- `cost`
- `failure_rate`

Indexes:

- index on `(evaluation_id, created_at)`
- index on `success`

#### `approval_requests`

- `id` UUID primary key
- `agent_run_id` UUID nullable foreign key to `agent_runs.id`
- `tool_call_id` UUID nullable
- `policy_decision` enum required default `REQUIRE_APPROVAL`
- `reason` text required
- `requested_action` jsonb required default `{}`
- `status` enum required default `PENDING`
- `requested_by` text nullable
- `reviewed_by` text nullable
- `reviewed_at` timestamptz nullable
- `created_at` timestamptz required
- `updated_at` timestamptz required

Indexes:

- index on `(status, created_at)`
- index on `(agent_run_id, created_at)`

Note: `tool_calls.approval_request_id` should be the direct foreign key for tool-level approvals. The nullable `tool_call_id` on `approval_requests` can be added after both tables exist or omitted if the reverse relation is unnecessary.

#### `deployment_events`

- `id` UUID primary key
- `agent_id` UUID foreign key to `agents.id`
- `from_agent_version_id` UUID nullable foreign key to `agent_versions.id`
- `to_agent_version_id` UUID nullable foreign key to `agent_versions.id`
- `event_type` enum required
- `reason` text nullable
- `metadata` jsonb required default `{}`
- `created_by` text nullable
- `created_at` timestamptz required

Indexes:

- index on `(agent_id, created_at)`
- index on `(event_type, created_at)`

### Local Docker Environment

Initial Compose services:

- `api`: FastAPI backend with hot reload.
- `worker`: Celery worker using the same backend image.
- `postgres`: PostgreSQL for local data.
- `redis`: Celery broker/result backend.
- `prometheus`: scrape API and worker metrics.
- `grafana`: dashboards and trace/metric panels.

Local environment files:

- `.env.example` documents all required settings.
- `.env` is local-only and gitignored.

Minimum environment variables:

```text
APP_ENV=local
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=postgresql+psycopg://agentops:agentops@postgres:5432/agentops
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
OTEL_SERVICE_NAME=ai-agent-control-plane-api
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
PROMETHEUS_METRICS_ENABLED=true
```

Docker deliverables for this milestone:

- `backend/Dockerfile`
- `docker-compose.yml`
- optional `docker-compose.observability.yml`
- healthchecks for API, Postgres, Redis
- `Makefile` targets for `dev`, `test`, `migrate`, `seed`, `lint`

Acceptance criteria:

- Repository layout exists.
- Backend project boots with an empty FastAPI health endpoint.
- PostgreSQL and Redis start locally.
- Alembic can connect to PostgreSQL.
- First migration creates the schema.
- Test harness can run in Docker and locally.

## Milestone 1: Backend Skeleton and Persistence

Goal: establish the backend application, migrations, and database access patterns.

Scope:

- FastAPI app bootstrap.
- Settings management.
- Structured logging.
- Database session lifecycle.
- SQLAlchemy models for all required tables.
- Alembic initial migration.
- Pydantic request/response schemas.
- Repository interfaces and implementations.
- Health and readiness endpoints.

Initial endpoints:

- `GET /health`
- `GET /ready`

Testing:

- Unit tests for settings.
- Database model smoke tests.
- Migration upgrade/downgrade test.
- Repository CRUD tests using test database.

Acceptance criteria:

- Backend runs locally.
- `alembic upgrade head` succeeds.
- Test suite passes.
- Schema matches the spec tables.

## Milestone 2: Agent Registry MVP

Goal: support agent creation, versioning, promotion metadata, and deprecation.

Scope:

- Create agent.
- List agents.
- Get agent by ID.
- Create new agent version.
- View versions.
- Update draft version metadata.
- Deprecate version.
- Promote lifecycle state without production deployment behavior yet.

Required endpoints:

- `POST /api/v1/agents`
- `GET /api/v1/agents`
- `GET /api/v1/agents/{id}`
- `POST /api/v1/agents/{id}/versions`
- `GET /api/v1/agents/{id}/versions`
- `PATCH /api/v1/agents/{id}/versions/{version_id}`
- `POST /api/v1/agents/{id}/versions/{version_id}/deprecate`

Testing:

- Agent creation validation.
- Duplicate name handling.
- Version number sequencing.
- Lifecycle transition validation.
- Repository and API tests.

Acceptance criteria:

- Agents and versions are fully persisted.
- Invalid lifecycle transitions fail with clear API errors.
- Agent registry APIs are stable enough for later frontend work.

## Milestone 3: Runtime and Tool Framework MVP

Goal: execute agent tasks through a controlled runtime and record every operational event.

Scope:

- Agent run creation.
- Synchronous MVP run execution for simple paths.
- Celery async execution for longer-running runs.
- Runtime state transitions.
- Tool abstraction with standard input/output/error shape.
- FileTool implementation.
- BrowserTool mock.
- EmailTool mock.
- TerminalTool sandboxed mock.
- Tool call logging.
- Runtime trace event persistence.

Required endpoints:

- `POST /api/v1/runs`
- `GET /api/v1/runs/{id}`
- `GET /api/v1/runs`

Testing:

- Run status transitions.
- Tool invocation recording.
- Failure recording.
- Latency calculation.
- Token/cost placeholder accounting.
- Celery task smoke test.

Acceptance criteria:

- A run can be created and executed.
- Tool calls are persisted and auditable.
- Failed tools do not disappear into logs only.
- Runtime captures `start_time`, `end_time`, `latency`, `token_count`, and `estimated_cost`.

## Milestone 4: Safety Gateway and Approval Queue

Goal: enforce policy decisions before tool execution and support human approval workflows.

Scope:

- Policy engine with explicit rules.
- Default policies:
  - read file: `ALLOW`
  - send email: `REQUIRE_APPROVAL`
  - delete filesystem: `DENY`
  - terminal command: `REQUIRE_APPROVAL` or `DENY` depending on command category
- Approval request creation.
- Approve/reject workflow.
- Blocked run behavior.
- Resume behavior after approval for MVP-safe paths.
- Policy trace events.

Required endpoints:

- `GET /api/v1/approvals`
- `GET /api/v1/approvals/{id}`
- `POST /api/v1/approvals/{id}/approve`
- `POST /api/v1/approvals/{id}/reject`

Testing:

- Allow path executes.
- Require approval path creates pending approval.
- Deny path blocks execution and records reason.
- Approving allows eligible action to resume.
- Rejecting marks request rejected and run blocked/failed as designed.

Acceptance criteria:

- Runtime cannot bypass Safety Gateway.
- Approval queue is queryable through API.
- Every policy check is traceable.

## Milestone 5: Trace and Observability APIs

Goal: make execution timelines and failure inspection available through backend APIs.

Scope:

- OpenTelemetry instrumentation for FastAPI, SQLAlchemy, Celery, service methods, and tool calls.
- Trace persistence for required event types:
  - `AgentRun`
  - `LLMCall`
  - `ToolCall`
  - `PolicyCheck`
  - `Evaluation`
- Trace lookup by trace ID.
- Run timeline API.
- Failure inspection API.
- Prometheus metrics endpoint.

Required endpoints:

- `GET /api/v1/traces/{trace_id}`
- `GET /api/v1/runs/{id}/timeline`
- `GET /api/v1/runs/{id}/failures`
- `GET /metrics`

Testing:

- Trace rows emitted for run, tool, and policy events.
- Timeline is ordered by timestamp.
- Failure API returns failed tool and policy context.
- Metrics endpoint exposes expected counters/histograms.

Acceptance criteria:

- Every execution has queryable trace data.
- API and worker emit metrics.
- Observability is functional locally before frontend work begins.

## Milestone 6: Evaluation Harness MVP

Goal: evaluate agent versions, store history, compare versions, and detect regressions.

Scope:

- Evaluation suite file format under `evals/suites`.
- Evaluation execution via Celery.
- Per-case result persistence.
- Aggregate metric computation:
  - `success_rate`
  - `tool_accuracy`
  - `latency`
  - `cost`
  - `failure_rate`
- v1 vs v2 comparison.
- Regression report generation.
- Evaluation trace events.

Required endpoints:

- `POST /api/v1/evaluations`
- `GET /api/v1/evaluations/{id}`
- `GET /api/v1/evaluations`
- `GET /api/v1/evaluations/{id}/report`
- `POST /api/v1/evaluations/compare`

Testing:

- Suite parser validation.
- Evaluation result persistence.
- Aggregate metric correctness.
- Comparison report correctness.
- Regression threshold behavior.

Acceptance criteria:

- A sample evaluation suite can run against an agent version.
- Evaluation history is queryable.
- v1 vs v2 report identifies regressions.

## Milestone 7: Deployment Control MVP

Goal: enforce deployment lifecycle and rollback controls.

Scope:

- Lifecycle transitions:
  - `DRAFT -> EVALUATED -> APPROVED -> PRODUCTION`
- Promotion rules:
  - `success_rate > threshold`
  - latest evaluation passed
- Rollback rules:
  - production failure rate exceeds threshold
  - latency exceeds threshold
- Deployment event history.
- Single production version per agent.

Required endpoints:

- `POST /api/v1/deployments/promote`
- `POST /api/v1/deployments/rollback`
- `GET /api/v1/agents/{id}/deployments`

Testing:

- Promotion denied without evaluation.
- Promotion allowed when thresholds pass.
- Production version uniqueness.
- Rollback creates deployment event.
- Rollback points production back to previous approved version.

Acceptance criteria:

- Deployment state is controlled by rules, not direct row edits.
- Deployment events provide an audit log.
- Backend MVP is complete after this milestone if tests and docs are current.

## Milestone 8: Backend Hardening and Documentation

Goal: stabilize the backend before beginning frontend or Terraform.

Scope:

- Seed data.
- Sample evaluation suite.
- README local setup.
- Architecture document and diagram.
- API examples.
- Error response standardization.
- Pagination and filtering for list endpoints.
- Basic auth placeholder or service-token guard if needed.
- Test coverage pass.
- Docker Compose end-to-end smoke test.

Acceptance criteria:

- New developer can run API, worker, Postgres, Redis, migrations, and seed data from README.
- Backend MVP APIs are documented.
- Backend MVP tests pass locally and in Docker.
- Frontend and Terraform work can start without changing backend fundamentals.

## Milestone 9: Frontend Dashboard

Do not start this milestone until backend MVP is complete.

Goal: build the dashboard on stable backend APIs.

Pages from specification:

- Agent Registry
- Execution History
- Evaluation Results
- Trace Viewer
- Approval Queue
- Metrics Dashboard

Display requirements:

- success rate
- failures
- average latency
- cost trends
- tool usage

Acceptance criteria:

- Frontend consumes real backend APIs.
- No mock-only dashboard screens remain for required MVP flows.
- Approval workflows can be completed from UI.
- Trace viewer renders execution timelines.

## Milestone 10: Terraform and AWS Infrastructure

Do not start this milestone until backend MVP is complete.

Goal: codify deployable AWS infrastructure.

Likely resources:

- VPC/networking
- ECS or EKS service for API and worker
- RDS PostgreSQL
- ElastiCache Redis
- Load balancer
- CloudWatch log groups
- IAM roles
- Secrets Manager parameters
- S3 bucket for artifacts/evaluation fixtures if needed
- Managed Prometheus/Grafana or equivalent observability path

Acceptance criteria:

- Terraform plan is reproducible.
- Environment variables and secrets are externalized.
- API and worker can be deployed independently.
- Database migrations have a safe deployment path.

## Backend MVP Definition of Done

Backend MVP is complete when:

- All required database tables exist through Alembic migrations.
- Agent registry APIs support agents and versions.
- Agent runtime can create and execute runs.
- Tool framework includes FileTool, BrowserTool mock, EmailTool mock, and TerminalTool sandboxed mock.
- Tool invocations are logged, traced, and auditable.
- Safety Gateway enforces `ALLOW`, `REQUIRE_APPROVAL`, and `DENY`.
- Approval queue supports approve/reject workflows.
- Evaluation harness stores history and compares versions.
- Regression reports are generated.
- OpenTelemetry and Prometheus are wired locally.
- Deployment promotion and rollback rules are enforced.
- Seed data and sample evaluation suite exist.
- Tests pass locally and in Docker.
- README explains local development.

Only after this point should frontend and Terraform implementation begin.

## Recommended Build Order

1. Create backend package, pyproject, config, health endpoints, Docker Compose.
2. Add SQLAlchemy models and Alembic initial migration.
3. Implement repositories and schemas.
4. Implement Agent Registry.
5. Implement Runtime and Tool Framework.
6. Add Safety Gateway and approvals.
7. Add trace persistence and OpenTelemetry instrumentation.
8. Add Evaluation Harness.
9. Add Deployment Control.
10. Harden backend with seed data, docs, metrics, and tests.
11. Build frontend dashboard.
12. Add Terraform/AWS deployment.

