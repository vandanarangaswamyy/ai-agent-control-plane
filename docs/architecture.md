# Architecture

The implementation follows the approved roadmap and is currently limited to Milestone 0.

## Layers

- API routes accept HTTP requests and delegate to dependencies or services.
- Services contain application behavior.
- Repositories will isolate persistence when domain behavior is introduced.
- Database modules own SQLAlchemy base classes, engine creation, and session lifecycle.
- Core modules own process-level configuration, logging, security hooks, and telemetry hooks.

## Current Scope

Milestone 0 establishes the repository structure, FastAPI app bootstrap, configuration, logging, SQLAlchemy setup, Alembic migration framework, Docker Compose environment, and local developer commands.

Business workflows are intentionally absent until the matching roadmap milestones.

