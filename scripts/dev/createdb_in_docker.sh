#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

SIGOPT_SERVER_CONFIG_DIR="${1:-config/development/}"
export SIGOPT_SERVER_CONFIG_DIR
shift || true

./scripts/launch/compose.sh run --rm createdb \
  python -m zigopt.utils.create_database "$@"
