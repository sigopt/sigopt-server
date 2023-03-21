#!/usr/bin/env bash
set -e
set -o pipefail
. scripts/launch/setup_env "$@"
./scripts/launch/compose.sh run --rm repl
