#!/usr/bin/env bash
set -e
set -o pipefail

export COMPOSE_PROJECT_NAME=sigopt-server-deploy
export SIGOPT_CONFIG_FILE=config/development.json
export TAG=latest
docker-compose --file=docker-compose.yml up --detach \
  minio \
  postgres \
  redis
docker-compose --file=docker-compose.yml up --detach \
  nginx
docker-compose --file=docker-compose.yml up \
  api \
  nginx \
  qworker \
  qworker-analytics \
  web-server \
  --scale=api=2 \
  --scale=qworker=2 \
  --scale=web-server=2
