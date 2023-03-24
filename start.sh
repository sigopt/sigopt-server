#!/usr/bin/env bash
set -e
set -o pipefail

export COMPOSE_PROJECT_NAME=sigopt-server-deploy
export sigopt_server_config_file="${sigopt_server_config_file:-config/sigopt.yml}"
export TAG=latest
MINIO_ROOT_PASSWORD="$(./tools/secure/generate_random_string.sh)"
export MINIO_ROOT_PASSWORD
docker-compose --file=docker-compose.yml up --detach \
  minio \
  nginx \
  postgres \
  redis
docker-compose --file=docker-compose.yml up \
  api \
  nginx \
  qworker \
  qworker-analytics \
  web-server \
  --scale=api=2 \
  --scale=qworker=2 \
  --scale=web-server=2
