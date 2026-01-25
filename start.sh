#!/usr/bin/env bash
set -Eeuo pipefail

# Railway uses $PORT. Do NOT hardcode.
# BOT_TOKEN must be set in Railway Variables.

cd "$(dirname "$0")"

: "${BOT_TOKEN:?BOT_TOKEN is required}"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-${PORT:-8000}}"          # Railway provides PORT; fallback 8000 for local
LOG_LEVEL="${LOG_LEVEL:-info}"
INITDATA_MAX_AGE_SECONDS="${INITDATA_MAX_AGE_SECONDS:-300}"

export INITDATA_MAX_AGE_SECONDS

# Railway = production: no --reload
exec uvicorn backend:app \
  --host "$HOST" \
  --port "$PORT" \
  --log-level "$LOG_LEVEL"