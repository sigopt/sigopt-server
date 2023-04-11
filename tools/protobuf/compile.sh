#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

ARGS=()
if which protoc-gen-mypy &>/dev/null; then
  ARGS=( --mypy_out=src/python )
fi

mkdir -p src/python

find src/protobuf/zigopt/protobuf/gen -name '*.proto' -print0 | xargs -0 \
  protoc \
  -I=src/protobuf \
  -I=/usr/local/include \
  --python_out=src/python \
  "${ARGS[@]}"
