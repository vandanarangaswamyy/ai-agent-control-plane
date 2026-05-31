# AGENTS.md

Persistent project memory for future Codex sessions. Update this file whenever a milestone is completed.

## Project Purpose

AI Agent Control Plane is a backend-first AgentOps platform for deploying, evaluating, monitoring, and safely operating AI agents in production. It is not a chatbot. The platform is infrastructure for agent versioning, controlled execution, tool-call observability, safety policies, approvals, evaluations, deployment controls, regression detection, and rollback.

The source specification is `AI_Agent_Control_Plane_Codex_Spec.docx`. The approved implementation roadmap is `docs/implementation-roadmap.md`.

## Current Architecture

Backend stack:

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 style ORM
- PostgreSQL
- Alembic
- Celery
- Redis
- Pydantic v2
- uv for dependency management and virtual environments
- Pytest

Repository layout:

- `backend/app/api`: FastAPI routes and dependency wiring.
- `backend/app/core`: config, logging, security/telemetry placeholders.
- `backend/app/db`: SQLAlchemy base, session, ORM models.
- `backend/app/domain`: enums and service-layer errors.
- `backend/app/repositories`: persistence layer. Repositories should not own business rules or commits.
- `backend/app/schemas`: Pydantic request/response models.
- `backend/app/services`: business logic and transaction boundaries.
- `backend/app/tools`: MVP tool framework.
- `backend/app/workers`: Celery app and tasks.
- `backend/alembic/versions`: database migrations.
- `backend/tests`: API and service tests.

Important architectural rules:

- API routes stay thin.
- Business logic lives in services.
- Persistence logic lives in repositories.
- Services own commit/rollback.
- Use dependency injection from `backend/app/api/deps.py`.
- Use UUID primary keys.
- Use Alembic for all schema changes.
- Use `uv`; do not add `requirements.txt` unless external tooling explicitly requires it.

## Milestone History

### Milestone 0: Foundation

Completed and merged to `main`.

Delivered:

- Repository structure.
- FastAPI bootstrap.
- `pyproject.toml` and `uv.lock`.
- Dockerfile and Docker Compose with Postgres and Redis.
- Environment-based settings.
- Structured logging.
- SQLAlchemy base/session.
- Alembic framework.
- Health/readiness endpoints.
- Makefile and README.

### Milestone 1: Agent Registry

Completed and merged to `main`.

Delivered:

- `agents` table.
- `agent_versions` table.
- Agent and version SQLAlchemy models.
- Alembic migration `202605310001_create_agent_registry.py`.
- Agent Registry repository/service/API.
- Pydantic schemas.
- Error handling.
- Tests.

Capabilities:

- Create agent.
- List agents.
- Get agent by ID.
- Create new agent version.
- List versions.
- Update draft version metadata.
- Deprecate version.

Rules implemented:

- Agent names are globally unique, case-insensitive.
- Version numbers auto-increment per agent.
- Only `DRAFT` versions can be edited.
- `DEPRECATED` versions cannot be edited.
- Invalid lifecycle transitions are rejected.

### Milestone 2: Runtime and Tool Framework

Completed and merged to `main`.

Delivered:

- `agent_runs` table.
- `tool_calls` table.
- `traces` table.
- Runtime SQLAlchemy models.
- Alembic migration `202605310002_create_runtime_tables.py`.
- Runtime repository/service/API.
- Tool framework:
  - `BaseTool`
  - `FileTool`
  - `BrowserTool` mock
  - `EmailTool` mock
  - `TerminalTool` sandboxed mock
- Celery task for async run execution.
- Synchronous run execution path for development.
- Tests.

Capabilities:

- Create run for a specific agent version.
- Execute run.
- Track `PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `BLOCKED`.
- Record start/end time, latency, output, error, token count, estimated cost.
- Persist tool call records.
- Persist trace events.

Trace events implemented:

- `AgentRunStarted`
- `AgentRunCompleted`
- `AgentRunFailed`
- `ToolInvoked`
- `ToolSucceeded`
- `ToolFailed`

### Milestone 3: Safety Gateway and Approval Queue

Completed and merged to `main`.

Delivered:

- `approval_requests` table.
- Approval SQLAlchemy model.
- Alembic migration `202605310003_create_approval_requests.py`.
- Policy engine.
- Safety Gateway service.
- Approval repository/service/API.
- Runtime integration so runtime no longer invokes tools directly.
- Tests.

Capabilities:

- Every tool invocation passes through `SafetyGateway`.
- Policy decisions:
  - `ALLOW`
  - `REQUIRE_APPROVAL`
  - `DENY`
- Default policies:
  - `FileTool`: `ALLOW`
  - `BrowserTool`: `ALLOW`
  - `EmailTool`: `REQUIRE_APPROVAL`
  - `TerminalTool`: `REQUIRE_APPROVAL`
- Approval states:
  - `PENDING`
  - `APPROVED`
  - `REJECTED`
  - `EXPIRED`
- Approval API:
  - `GET /api/v1/approvals`
  - `GET /api/v1/approvals/{id}`
  - `POST /api/v1/approvals/{id}/approve`
  - `POST /api/v1/approvals/{id}/reject`

Runtime behavior:

- `ALLOW`: execute tool immediately.
- `REQUIRE_APPROVAL`: create approval request, trace event, blocked tool call, and mark run `BLOCKED`.
- `DENY`: create trace event, block tool call/run, and do not execute tool.
- Approving resumes execution and completes/fails the run based on tool result.
- Rejecting leaves the run blocked.

Additional trace events:

- `PolicyCheck`
- `ApprovalRequested`
- `ApprovalApproved`
- `ApprovalRejected`
- `ToolBlocked`

### Milestone 4: Trace and Observability APIs

Completed on `feature/observability-apis`.

Delivered:

- Trace lookup API.
- Run timeline API.
- Run failure inspection API.
- Prometheus metrics endpoint.
- OpenTelemetry spans for FastAPI requests, runtime execution, safety checks, tool execution, and Celery tasks.
- Observability service/query layer.
- Tests for trace ordering, failure inspection, metrics, and span smoke checks.

Capabilities:

- Query persisted traces by `trace_id`.
- Inspect the chronological timeline of any run.
- Diagnose blocked, denied, and failed runs through structured failure responses.
- Expose operational counters and latency histograms at `/metrics`.

Current observability notes:

- Spans are collected locally with an in-memory exporter for MVP.
- Prometheus metrics are process-local and exposed through the app registry.

## Completed Features

- Backend foundation and local Docker environment.
- Agent Registry with versioned configurations.
- Runtime engine with synchronous and Celery execution paths.
- Tool framework with audited tool calls.
- Persistent trace events.
- Safety Gateway policy checks.
- Approval queue and approve/reject workflows.
- Trace lookup, run timeline, failure inspection, and metrics APIs.
- OpenTelemetry instrumentation foundation.
- Local test suite and migrations.

Current sanity checks on `main` after Milestone 3:

- `uv run pytest`: 25 passed, 1 warning.
- `uv run ruff check .`: all checks passed.
- `docker compose run --rm api uv run alembic upgrade head`: passed.

## Open Technical Debt

- Token and estimated cost accounting are deterministic placeholders.
- Runtime supports only one tool action per run.
- Policy rules are in-process; future work should make them persisted/configurable.
- Approval identity is passed in request body; real auth/user context is not implemented.
- `EXPIRED` approval state exists but no expiry scheduler is implemented.
- OpenTelemetry uses a local in-memory exporter; no external collector/export pipeline exists yet.
- Prometheus metrics are process-local only; no long-term metrics backend is configured.
- No evaluation harness yet.
- No deployment control/promotion/rollback yet.
- No frontend dashboard yet.
- No Terraform/AWS infrastructure yet.
- FastAPI/Starlette test client emits an `httpx` deprecation warning.

## Coding Standards

- Use Python type hints everywhere.
- Use Pydantic v2 models for API request/response contracts.
- Use SQLAlchemy 2.0 style.
- Use repository pattern for persistence.
- Use service layer pattern for business rules and transaction boundaries.
- Keep API routes thin.
- Add Alembic migrations for schema changes.
- Add tests for every business rule and API behavior.
- Prefer deterministic MVP behavior over external side effects.
- Mock or sandbox tools that could have external impact.
- Use `uv run pytest` and `uv run ruff check .` before commits.
- Use Docker Compose for Postgres-backed migration checks.

## Branch Strategy

- `main` contains approved and merged milestones.
- Each milestone gets a feature branch:
  - `feature/agent-registry`
  - `feature/runtime-tool-framework`
  - `feature/safety-gateway`
  - `feature/observability-apis`
- Commit milestone work on the feature branch.
- Push the feature branch.
- Run sanity checks before merge.
- Merge into `main` with a merge commit.
- Push `main`.

## Future Roadmap

Next approved roadmap steps:

1. Evaluation Harness:
   - Evaluation suites.
   - Evaluation execution via Celery.
   - Evaluation history.
   - Metrics: success rate, tool accuracy, latency, cost, failure rate.
   - v1 vs v2 comparisons.
   - Regression reports.

2. Deployment Control:
   - Lifecycle gates.
   - Promotion rules.
   - Rollback rules.
   - Deployment event history.

3. Backend hardening:
   - Seed data.
   - API docs/examples.
   - Pagination/filter consistency.
   - Auth placeholder or service-token guard.
   - More integration tests.

4. Frontend Dashboard:
   - Do not start until backend MVP is complete.

5. Terraform/AWS:
   - Do not start until backend MVP is complete.

## Notes For Future Agents

- Do not redesign the system unless explicitly asked.
- Follow `docs/implementation-roadmap.md`.
- Respect milestone boundaries.
- Update this file after each completed milestone.
- Before changing code, inspect the relevant service/repository/API patterns already present.
- Do not implement frontend or Terraform before backend MVP completion.
