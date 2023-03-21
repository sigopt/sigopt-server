#!/usr/bin/env bash
set -e
set -o pipefail
. scripts/launch/setup_env.sh
./scripts/launch/compose.sh stop "${PERSISTENT_SERVICES[@]}"
