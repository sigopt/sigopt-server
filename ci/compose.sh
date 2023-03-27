#!/usr/bin/env bash
set -e
set -o pipefail

export COMPOSE_PROJECT_NAME="${CIRCLE_SHA1}_${CIRCLE_JOB}_${CIRCLE_NODE_INDEX}"
export TAG="$CIRCLE_SHA1"
export sigopt_server_config_file=config/circleci.json
export MINIO_ROOT_PASSWORD=CHANGEME123

exec docker-compose --file=docker-compose.yml --env-file=./.env "$@"
