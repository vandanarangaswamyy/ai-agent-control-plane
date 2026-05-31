# AI Agent Control Plane

Backend-first implementation of the AI Agent Control Plane specification.

Current implementation status: Milestone 0 foundation only. Agent Registry, Runtime, Tools, Safety Gateway, Evaluations, Dashboard, and Terraform are intentionally not implemented yet.

## Requirements

- Docker and Docker Compose
- `uv`
- Python 3.12+ for local backend development outside Docker

## Local Startup

1. Create local environment configuration:

   ```bash
   cp .env.example .env
   ```

2. Start local services:

   ```bash
   make dev
   ```

3. For host-based backend development, create/update the local virtual environment:

   ```bash
   make sync
   ```

4. In another terminal, run migrations:

   ```bash
   make migrate
   ```

5. Check service health:

   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/ready
   ```

## Common Commands

```bash
make dev
make down
make logs
make sync
make migrate
make revision MSG="create initial schema"
make test
make shell
```

Dependencies are managed through `uv`, `backend/pyproject.toml`, and `backend/uv.lock`. Do not generate `requirements.txt` unless a specific external tool requires it.

## Backend Structure

```text
backend/app/api       FastAPI routers and dependency wiring
backend/app/core      Configuration, logging, and process-level concerns
backend/app/db        SQLAlchemy base classes and session management
backend/app/domain    Domain enums, errors, and value objects
backend/app/services  Business-service layer
backend/app/workers   Celery bootstrap
backend/alembic       Alembic migration environment
```

API routes should remain thin. Business rules belong in services, persistence details belong in repositories, and database lifecycle belongs in `app.db`.

## Milestone Boundary

Do not add Agent Registry business logic, Runtime behavior, Tools, Safety Gateway, Evaluations, Dashboard, or Terraform until Milestone 0 is reviewed and approved.
