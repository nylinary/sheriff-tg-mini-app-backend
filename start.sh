#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# Run DB migrations (safe to run on every start)
python -m alembic upgrade head

exec uvicorn main:app --host 0.0.0.0 --port "${PORT}" --log-level "${LOG_LEVEL}"