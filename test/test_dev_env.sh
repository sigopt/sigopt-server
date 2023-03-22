#!/usr/bin/env bash
set -e
set -o pipefail

. scripts/launch/setup_env.sh "${sigopt_server_config_file:-config/development.json}"
./scripts/launch/compose.sh run --rm generate-routes
./scripts/launch/compose.sh run --rm --publish=5900:5900 test-runner python -m test.test_runner --config-file "$sigopt_server_config_file" "$@"
