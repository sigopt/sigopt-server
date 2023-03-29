#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

ISORT_ARGS=('-c')
PROVIDED_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fix)
      ISORT_ARGS=()
      shift
      ;;
    *)
      PROVIDED_ARGS+=("$1")
      shift
      ;;
  esac
done

git ls-files \
  | grep '\.py$' \
  | xargs ./pp isort --settings tools/lint/python/isort.cfg --ac "${ISORT_ARGS[@]}" "${PROVIDED_ARGS[@]}" --filter-files
