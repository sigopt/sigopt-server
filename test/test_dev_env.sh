#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

. scripts/launch/setup_env.sh "${SIGOPT_SERVER_CONFIG_DIR:-./config/development/}"
./scripts/launch/compose.sh run --rm generate-routes
./scripts/launch/compose.sh run --rm --publish=5900:5900 test-runner python -m test.test_runner --config-dir "$SIGOPT_SERVER_CONFIG_DIR" "$@"
