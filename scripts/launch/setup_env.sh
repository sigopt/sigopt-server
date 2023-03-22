#!/usr/bin/env bash
# no_set_e
# no_pipefail

sigopt_server_config_file="${1:-config/development.json}"
export sigopt_server_config_file="${sigopt_server_config_file}"
export COMPOSE_HTTP_TIMEOUT=86400

export PERSISTENT_SERVICES=(
  postgres
  redis
  minio
)
