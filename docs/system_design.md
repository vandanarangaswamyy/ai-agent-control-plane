# System Design

This system uses clean architecture to keep the platform maintainable as the number of workflows grows. The codebase is structured around stable boundaries: API, service, repository, schema, and database layers.

## Architectural Decisions

- Business logic lives in services, not routes.
- Persistence logic lives in repositories, not services.
- Request and response contracts are explicit Pydantic v2 schemas.
- SQLAlchemy 2.0 ORM models represent the operational data model.
- Alembic owns all schema changes.
- Celery is used for asynchronous execution where runtime work can be deferred.
- Observability is built from persisted traces, not ephemeral logs alone.
- Tools are mocked or sandboxed in MVP to avoid external side effects.

## Repository Pattern Usage

Repositories are small persistence adapters:

- They encapsulate SQLAlchemy statements.
- They return ORM objects or simple lists.
- They do not commit transactions.
- They do not apply lifecycle rules.

This keeps query logic close to the data model and leaves behavior to services.

## Service Layer Usage

Services are the application boundary:

- `AgentRegistryService` manages agents and version lifecycle.
- `RuntimeService` manages run creation, execution, and trace persistence.
- `SafetyGateway` evaluates tool policies and approval requirements.
- `EvaluationService` executes suites and compares versions.
- `DeploymentService` promotes, rolls back, and records deployment events.
- `ObservabilityService` reconstructs timelines and failure reports from persisted data.

Each service owns its own business invariants and transaction flow.

## Dependency Injection Approach

- FastAPI dependencies are centralized in `app/api/deps.py`.
- Route handlers receive services through `Depends(...)`.
- Service construction happens in one place so wiring is consistent across API routes and tests.
- Tests can override dependencies cleanly without patching implementation internals.

## Scalability Considerations

- Operational records are persisted in PostgreSQL with indexed access paths for common lookup shapes.
- Runtime, evaluation, and deployment history are append-friendly data models.
- Long-running execution can move to Celery without changing the service contract.
- The API can scale horizontally because the state lives in the database and Redis, not in the web process.
- Trace and metrics queries are read-only projections that can later be moved to dedicated observability infrastructure if needed.

## Tradeoffs

- Evaluation suites are stored as JSON files for now instead of a database-backed suite catalog.
- Observability uses local Prometheus exposition and in-memory OpenTelemetry export for MVP simplicity.
- Approval review identity is still request-body based rather than tied to a full auth system.
- Deployment promotion uses a configurable threshold rather than a persisted policy engine.
- Runtime currently supports one tool action per run, which keeps the execution model simple.

## Future Evolution

- Persist policy configuration instead of hardcoding defaults in code.
- Add a real auth layer for approvals and deployment actions.
- Move evaluation suites into a versioned persisted catalog if suite management becomes operationally important.
- Expand runtime execution into richer multi-step orchestration.
- Replace local-only observability export with a collector-backed pipeline when deployment environments require it.
- Add frontend and infrastructure layers only after the backend contract stabilizes.
