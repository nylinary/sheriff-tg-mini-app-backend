#!/usr/bin/env bash
set -euo pipefail

exec uvicorn backend:app --host 0.0.0.0 --port "${PORT}" --log-level "${LOG_LEVEL:-info}"