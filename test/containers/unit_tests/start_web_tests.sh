#!/usr/bin/env bash
set -e
set -o pipefail

JUNIT_OUTPUT_DIR="/sigopt-server/artifacts/test/unit_tests/web"
export JEST_JUNIT_OUTPUT="${JUNIT_OUTPUT_DIR}/junit.xml"

yarn test
