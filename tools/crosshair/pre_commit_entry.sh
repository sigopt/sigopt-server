#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

source scripts/set_python_path.sh .
printf "%s\0" "$@" | xargs -0 -n1 ./tools/crosshair/main.py check \
  --per_path_timeout=0.01 \
  --per_condition_timeout=2 \
  --analysis_kind=deal
