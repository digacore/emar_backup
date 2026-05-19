#!/usr/bin/env bash
# Restart file_api and verify health (run on production host from web/).
set -euo pipefail

cd "$(dirname "$0")/.."
PORT="${FILE_API_PORT:-33000}"

echo "==> file_api container status"
docker compose ps file_api

echo "==> last 50 log lines"
docker compose logs file_api --tail 50

echo "==> rebuild and start file_api"
docker compose up -d --build file_api

echo "==> waiting for health (up to 60s)"
for i in $(seq 1 12); do
  if curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    echo "OK: http://127.0.0.1:${PORT}/health"
    curl -s "http://127.0.0.1:${PORT}/health"
    echo
    exit 0
  fi
  sleep 5
done

echo "FAILED: health check did not pass"
docker compose logs file_api --tail 100
exit 1
