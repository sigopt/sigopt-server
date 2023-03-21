#!/usr/bin/env bash
set -e
set -o pipefail

if [ $# -eq 0 ]; then
  >&2 echo "No test files provided!"
  >&2 echo "There might be an issue with circleci's test splitting."
  exit 1
fi

SUITE="$1"
shift

./ci/compose.sh run --name=test-runner test-runner \
  python -m test.test_runner \
    --config-file config/circleci.json \
    --skip-compile \
    --junitxml="junit-results/$SUITE/junit.xml" \
    "$@"
