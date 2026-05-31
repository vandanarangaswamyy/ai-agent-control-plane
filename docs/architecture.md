# Architecture

This project is a backend-first AgentOps control plane. It manages agent versions, runtime execution, safety approvals, evaluation runs, observability, and deployment promotion through a clean service-oriented backend.

## High-Level Architecture

```mermaid
flowchart LR
    Client[API Client] --> API[FastAPI /api/v1]
    API --> SRV[Service Layer]
    SRV --> REPO[Repository Layer]
    REPO --> DB[(PostgreSQL)]
    SRV --> TOOLS[Mocked / Sandboxed Tools]
    SRV --> CELERY[Celery Workers]
    CELERY --> REDIS[(Redis)]
    SRV --> TRACES[Trace Persistence]
    SRV --> METRICS[Prometheus Metrics]
    SRV --> OTel[OpenTelemetry]
```

## Component Responsibilities

- `app/api`: HTTP routing, request validation, response serialization, dependency injection.
- `app/services`: business rules, orchestration, transaction boundaries, workflow state transitions.
- `app/repositories`: SQLAlchemy persistence only, no business decisions.
- `app/db`: SQLAlchemy base classes, session handling, ORM models.
- `app/tools`: executable tool abstractions and mocks.
- `app/workers`: async execution entry points for Celery.
- `app/core`: configuration, logging, telemetry, metrics.

## Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API Route
    participant S as Service
    participant R as Repository
    participant D as PostgreSQL

    C->>A: HTTP request
    A->>S: call service dependency
    S->>R: read/write operations
    R->>D: SQLAlchemy query/flush
    D-->>R: persisted data
    R-->>S: ORM objects
    S-->>A: domain result
    A-->>C: JSON response
```

## Runtime Flow

```mermaid
flowchart TD
    Run[Create Run] --> Start[Mark RUNNING]
    Start --> Safety[Safety Gateway Policy Check]
    Safety -->|ALLOW| Tool[Tool Execute]
    Safety -->|REQUIRE_APPROVAL| Approval[Create Approval Request]
    Safety -->|DENY| Block[Block Run]
    Approval --> Resume[Approve / Reject Workflow]
    Tool --> Result[Persist Tool Call + Trace]
    Result --> Complete[Mark SUCCESS or FAILED]
    Block --> Trace[Persist Block Trace]
```

## Safety Approval Workflow

```mermaid
flowchart TD
    ToolCall[Tool Invocation] --> Check[Policy Check]
    Check -->|ALLOW| Exec[Execute Tool]
    Check -->|REQUIRE_APPROVAL| Request[Create Approval Request]
    Check -->|DENY| Reject[Persist Blocked Trace]
    Request --> Pending[Run BLOCKED]
    Pending --> Decision{Human Review}
    Decision -->|Approve| Resume[Resume Run]
    Decision -->|Reject| Stop[Remain Blocked]
    Resume --> Exec
```

## Evaluation Flow

```mermaid
flowchart TD
    Suite[Load Suite JSON] --> Eval[Create Evaluation]
    Eval --> Cases[Execute Cases]
    Cases --> Runtime[Reuse Runtime + Safety + Tools]
    Runtime --> Results[Persist Evaluation Results]
    Results --> Metrics[Compute Metrics]
    Metrics --> Report[Persist Report]
    Report --> Compare[Optional Version Comparison]
```

## Deployment Flow

```mermaid
flowchart TD
    EvalCheck[Latest Evaluation Gate] -->|PASS + threshold met| Promote[Promote Version]
    EvalCheck -->|Fail or missing| Deny[Reject Promotion]
    Promote --> Demote[Demote Previous Production Version]
    Demote --> Event[Persist Deployment Event]
    Event --> Trace[Persist Deployment Trace]
    Promote --> Production[Single PRODUCTION Version]
    Production --> Rollback[Rollback to Previous Candidate]
```

## Observability Flow

```mermaid
flowchart TD
    App[API + Services + Workers] --> Traces[Trace Persistence]
    App --> Metrics[Prometheus Registry]
    App --> OTel[OpenTelemetry Spans]
    Traces --> Timeline[Timeline API]
    Traces --> Failures[Failure Inspection API]
    Metrics --> Export[/metrics/]
```

## Milestone Coverage

- Agent Registry owns versioned agent configuration.
- Runtime owns run lifecycle and tool call auditing.
- Safety Gateway owns policy-gated execution and approvals.
- Observability owns trace lookup, timeline, failure analysis, and metrics.
- Evaluation Harness owns suite execution, result persistence, and regression comparison.
- Deployment Control owns promotion, rollback, and production assignment.

## Implementation Notes

- API routes are thin and delegate immediately to services.
- Service methods own transaction boundaries and write orchestration.
- Repositories never decide whether an operation is allowed.
- The system persists operational data before exposing it through query APIs.
- Tools remain mocked or sandboxed for MVP safety.
