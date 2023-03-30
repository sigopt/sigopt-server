#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

for _ in {1..30}; do
  if x11vnc -forever -shared -quiet -geometry "$GEOMETRY" -display "$DISPLAY" >/dev/null; then
    break
  fi
  sleep 1
done
