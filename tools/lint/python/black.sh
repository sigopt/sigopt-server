#!/usr/bin/env bash
set -e
set -o pipefail

black --config=tools/lint/python/pyproject.toml --experimental-string-processing "$@"
