#!/usr/bin/env bash
set -e
set -o pipefail

function m {
  echo "--mount=type=bind,source=$(pwd)/$1,target=/sigopt-server/$1"
}

docker run -i --rm \
  "$(m scripts)" \
  "$(m src)" \
  "$(m test)" \
  "$(m tools)" \
  --workdir=/sigopt-server \
  sigopt/python:latest \
  ./tools/protobuf/compile.sh
