#!/usr/bin/env sh
set -eu

cd backend
uv run pytest
