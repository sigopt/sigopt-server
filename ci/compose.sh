#!/usr/bin/env bash
set -e
set -o pipefail

export COMPOSE_PROJECT_NAME="${CIRCLE_SHA1}_${CIRCLE_JOB}_${CIRCLE_NODE_INDEX}"

export TEST_RUNNER_NAME="${TEST_RUNNER_NAME:-test-runner}"

exec docker-compose --file=ci/docker-compose.yml --env-file=./.env "$@"
