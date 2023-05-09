#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

export TAG="$CIRCLE_SHA1"
export MINIO_ROOT_PASSWORD=CHANGEME123
export ENABLE_CONTRACTS=x

exec docker compose --file=docker-compose.yml --env-file=./.env "$@"
