#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

source .env
docker build . --tag=sigopt/nginx:scan --file=docker/images/nginx/Dockerfile \
  --build-arg=NGINX_VERSION="$NGINX_VERSION"
docker build . --tag=sigopt/web:scan --file=docker/images/web/Dockerfile
docker build . --tag=sigopt/zigopt:scan --file=docker/images/zigopt/Dockerfile \
  --build-arg=PROTOBUF_VERSION="$PROTOBUF_VERSION"

mkdir -p artifacts/trivy
python ./docker/scan_application_images.py --registry=sigopt --tag=scan -- "$@"
