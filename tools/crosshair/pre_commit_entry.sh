#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

if [ -z "$_RUN_CROSSHAIR" ]; then
  if crosshair check \
    --per_path_timeout=0.01 \
    --per_condition_timeout=2 \
    --analysis_kind=deal \
    "$@"
  then
    exit
  else
    echo "The above failure occurred while checking $1"
    echo
    exit 1
  fi
fi


source scripts/set_python_path.sh .
printf "%s\0" "$@" | xargs -0 -n1 env _RUN_CROSSHAIR=x "$0"
