#!/usr/bin/env bash

set -euo pipefail

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: $name" >&2
    exit 1
  fi
}

require_env DEPLOY_ROOT
require_env STAGE_ENV_FILE
require_env BACKEND_ENV_FILE
require_env GHCR_USERNAME
require_env GHCR_TOKEN

COMPOSE_FILE="$DEPLOY_ROOT/deploy/docker-compose.stage.yml"

if docker compose version >/dev/null 2>&1; then
  COMPOSE_BIN=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_BIN=(docker-compose)
else
  echo "Neither 'docker compose' nor 'docker-compose' is available." >&2
  exit 1
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

if [[ ! -f "$STAGE_ENV_FILE" ]]; then
  echo "Stage env file not found: $STAGE_ENV_FILE" >&2
  exit 1
fi

if [[ ! -f "$BACKEND_ENV_FILE" ]]; then
  echo "Backend env file not found: $BACKEND_ENV_FILE" >&2
  exit 1
fi

set -a
. "$STAGE_ENV_FILE"
set +a

export STAGE_ENV_FILE
export BACKEND_ENV_FILE

echo "$GHCR_TOKEN" | docker login ghcr.io --username "$GHCR_USERNAME" --password-stdin

"${COMPOSE_BIN[@]}" -f "$COMPOSE_FILE" pull

"${COMPOSE_BIN[@]}" -f "$COMPOSE_FILE" up -d postgres

"${COMPOSE_BIN[@]}" -f "$COMPOSE_FILE" run --rm backend \
  alembic -c /app/backend/alembic.ini upgrade head

"${COMPOSE_BIN[@]}" -f "$COMPOSE_FILE" up -d

docker image prune --force --filter dangling=true
