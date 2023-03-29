#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

export NODE_DOMAIN=server
export NODE_OPTIONS="--max-old-space-size=2048"
exec yarn -s webpack \
  --config=web/js/webpack/server_side.config.babel.js \
  --env=NODE_ENV=production
