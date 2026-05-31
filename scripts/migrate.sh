#!/usr/bin/env sh
set -eu

cd backend
uv run alembic upgrade head
