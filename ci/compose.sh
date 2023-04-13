#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

export COMPOSE_PROJECT_NAME="${CIRCLE_SHA1}_${CIRCLE_JOB}_${CIRCLE_NODE_INDEX}"
export TAG="$CIRCLE_SHA1"
export SIGOPT_SERVER_CONFIG_DIR=/sigopt-server/config/circleci/
export MINIO_ROOT_PASSWORD=CHANGEME123

exec docker-compose --file=docker-compose.yml --env-file=./.env "$@"
