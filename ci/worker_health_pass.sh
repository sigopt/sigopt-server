#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

for container in qworker qworker-analytics; do
  if ./ci/compose.sh run --rm --no-deps -e QWORKER_HEALTH_CHECK=true "$container"; then
    echo "worker-health test for $container passed"
  else
    >&2 echo "worker-health test for $container failed!"
    exit 1
  fi
done
