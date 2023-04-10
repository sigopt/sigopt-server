#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

SETUP_ARGS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --no-workers) WORKERS=false; shift;; # disable qworkers
    --no-api) API=false; shift;; # disable the api
    --no-web) WEB=false; shift;; # disable the web
    --api-only) WEB=false; WORKERS=false; shift;; # only run api containers
    --web-only) API=false; WORKERS=false; shift;; # only run web containers
    --foreground) FOREGROUND=true; shift;;
    --documentation) DOCUMENTATION=true; shift;;
    *) SETUP_ARGS+=("$1"); shift;;
  esac
done

FOREGROUND_SERVICES=(protowatch nginx)
BACKGROUND_SERVICES=()

if "${WORKERS:-true}"; then
  FOREGROUND_SERVICES+=(qworker qworker-analytics)
fi

if "${API:-true}"; then
  FOREGROUND_SERVICES+=(api smtp)
fi

if "${WEB:-true}"; then
  FOREGROUND_SERVICES+=(web-client web-server)
fi

if "${FOREGROUND:-false}"; then
  FOREGROUND_SERVICES+=("${BACKGROUND_SERVICES[@]}")
  BACKGROUND_SERVICES=()
fi

if "${DOCUMENTATION:-false}"; then
  FOREGROUND_SERVICES=(documentation)
  BACKGROUND_SERVICES=()
fi

if [ ${#FOREGROUND_SERVICES[@]} -eq 0 ]; then
  >&2 echo "No services to launch in the foreground!"
  exit 1
fi

function setup_web {
  if "${WEB:-true}"; then
    ./scripts/launch/compose.sh run --rm init-web
  fi
}

function kill_services {
  ./scripts/launch/compose.sh kill \
    "${FOREGROUND_SERVICES[@]}" \
    "${BACKGROUND_SERVICES[@]}" &>/dev/null || true
}

function start_bg_services {
  if [ ${#BACKGROUND_SERVICES[@]} -gt 0 ]; then
    ./scripts/launch/compose.sh build "${BACKGROUND_SERVICES[@]}"
    ./scripts/launch/compose.sh up --detach "${BACKGROUND_SERVICES[@]}"
  fi
}

function start_fg_services {
  if [ ${#FOREGROUND_SERVICES[@]} -gt 0 ]; then
    ./scripts/launch/compose.sh build "${FOREGROUND_SERVICES[@]}"
    ./scripts/launch/compose.sh up -d "${FOREGROUND_SERVICES[@]}"
    ./scripts/launch/compose.sh logs -f "${FOREGROUND_SERVICES[@]}"
  fi
}

function main {
  . scripts/launch/setup_env.sh "$@"
  setup_web
  kill_services
  start_bg_services
  trap kill_services EXIT
  start_fg_services
}

main "${SETUP_ARGS[@]}"
