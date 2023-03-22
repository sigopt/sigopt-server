#!/usr/bin/env bash
set -e
set -o pipefail

make setup-integration-tests

exec ./pp test/test_runner.py "$@"
