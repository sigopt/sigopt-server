#!/usr/bin/env bash
set -e
set -o pipefail

source .env
docker build . --tag=sigopt/nginx:scan --file=docker/images/nginx/Dockerfile \
  --build-arg=NGINX_VERSION="$NGINX_VERSION"
docker build . --tag=sigopt/web:scan --file=docker/images/web/Dockerfile \
  --build-arg=NODE_VERSION="$NODE_VERSION"
docker build . --tag=sigopt/zigopt:scan --file=docker/images/zigopt/Dockerfile \
  --build-arg=PROTOBUF_VERSION="$PROTOBUF_VERSION" \
  --build-arg=PYTHON_VERSION="$PYTHON_VERSION"

mkdir -p artifacts/trivy
python ./docker/scan_application_images.py --registry=sigopt --tag=scan -- "$@"
