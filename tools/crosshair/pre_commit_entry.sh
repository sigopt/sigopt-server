#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

if [ -z "$_RUN_CROSSHAIR" ]; then
  OUTPUT="$(mktemp)"
  if crosshair check \
    --per_path_timeout=0.01 \
    --per_condition_timeout=2 \
    --analysis_kind=deal \
    "$@" &>"$OUTPUT"
  then
    exit
  fi
  echo "The above failure occurred while checking $1" >>"$OUTPUT"
  echo >>"$OUTPUT"
  cat "$OUTPUT"
  exit 1
fi


source scripts/set_python_path.sh .
printf "%s\0" "$@" | xargs -0 -n1 -P4 env _RUN_CROSSHAIR=x "$0"
