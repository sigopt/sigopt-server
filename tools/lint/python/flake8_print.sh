#!/usr/bin/env bash
set -e
set -o pipefail

# NOTE: version-dependent error code; 5.0.0+ use T201
PRINT_FOUND_ERROR_CODE=T001
git ls-files src/python/zigopt libsigopt | grep '\.py$' | xargs ./pp flake8 --select="${PRINT_FOUND_ERROR_CODE}" "$@"
