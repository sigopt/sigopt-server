#!/usr/bin/env bash
set -e
set -o pipefail

COMMAND=(./scripts/launch/all_live.sh --web-only --foreground "$@")

exec "${COMMAND[@]}"
