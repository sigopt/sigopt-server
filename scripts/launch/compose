#!/usr/bin/env bash
set -e
set -o pipefail

export COMPOSE_PROJECT_NAME=sigopt-server

export STATIC_DEV_SERVER_PORT=7800

HOSTNAME="$(hostname)"
export HOSTNAME

HOST_PWD="$(pwd)"
export HOST_PWD

exec docker compose --file=docker-compose.dev.yml "$@"
