#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

. scripts/launch/setup_env.sh "${sigopt_server_config_file:-config/development.json}"
./scripts/launch/compose.sh run --rm generate-routes
./scripts/launch/compose.sh run --rm --publish=5900:5900 test-runner python test/test_runner.py --config-file "$sigopt_server_config_file" "$@"
