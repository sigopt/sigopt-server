#!/usr/bin/env bash
set -e
set -o pipefail

function m {
  echo "--mount=type=bind,source=$(pwd)/$1,target=/sigopt-server/$1"
}

CONTAINER_NAME="yarn-command-$(date +%s)"
function cleanup {
  docker rm -f "$CONTAINER_NAME"
}
trap cleanup EXIT

docker run -ti --name="$CONTAINER_NAME" \
  "$(m package.json)" \
  "$(m yarn.lock)" \
  --workdir=/sigopt-server \
  sigopt/node:latest \
  yarn "$@"

docker commit "$CONTAINER_NAME" sigopt/node:latest
