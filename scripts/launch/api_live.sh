#!/usr/bin/env bash
set -e
set -o pipefail

COMMAND=(./scripts/launch/all_live.sh --no-web --foreground "$@")

exec "${COMMAND[@]}"
