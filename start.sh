#!/usr/bin/env bash
set -e
set -o pipefail

export SIGOPT_CONFIG_FILE=config/development.json
export TAG=latest
docker-compose --file=docker-compose.yml up \
  api \
  nginx \
  qworker \
  qworker-analytics \
  web-server
