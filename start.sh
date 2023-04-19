#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

export COMPOSE_PROJECT_NAME=sigopt-server
MINIO_ROOT_PASSWORD="$(./tools/secure/generate_random_string.sh)"
export MINIO_ROOT_PASSWORD
sigopt_server_version="git:$(git rev-parse HEAD)"
export sigopt_server_version
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
