#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# no_set_e
# no_pipefail

SIGOPT_SERVER_CONFIG_DIR="${1:-./config/development/}"
export SIGOPT_SERVER_CONFIG_DIR
export COMPOSE_HTTP_TIMEOUT=86400

export PERSISTENT_SERVICES=(
  postgres
  redis
  minio
)
