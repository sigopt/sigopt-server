#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

docker build -f docker/images/python-development/Dockerfile . -t sigopt/python-development:latest
./scripts/launch/compose.sh run --rm \
  sigopt/python-development:latest \
  ./tools/protobuf/compile.sh
