#!/usr/bin/env bash

set -e
set -o pipefail

docker create \
  --name=prettier \
  --mount="source=$(pwd),target=/sigopt-server/to-fix,type=bind,consistency=cached" \
  --workdir=/sigopt-server/to-fix \
  --entrypoint=/usr/bin/env \
  sigopt/node-development:latest \
  node /sigopt-server/node_modules/.bin/prettier "$@" \
  >/dev/null

trap 'docker rm -f prettier >/dev/null' EXIT

docker start prettier >/dev/null
docker logs -f prettier
