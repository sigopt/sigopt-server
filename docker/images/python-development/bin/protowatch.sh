#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

if [ -n "$_COMPILE" ]; then
  echo "compiling protobuf"
  if ! find /sigopt-server/src/protobuf -name '*.proto' -print0 | xargs -0 \
    protoc \
      -I=/sigopt-server/src/protobuf \
      --python_out=/sigopt-server/src/python
  then
    echo "compile protobuf failed!"
  fi
else
  _COMPILE=x run_command_on_change.py --dir=/sigopt-server/src/protobuf --initial-run "$0"
fi
