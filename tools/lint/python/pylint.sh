#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

: "${JOBS:=1}"
: "${RCFILE:=tools/lint/python/pylint.rc}"

function run_pylint {
  ./pp pylint \
    --output-format=text \
    --msg-template='{abspath}:{line}:{column}: [{category}:{symbol}] {obj}: {msg}' \
    --reports=n \
    --rcfile="$RCFILE" \
    --jobs="$JOBS" \
    -- \
    "$@"
}

if [ -n "$_NO_PARSE_ARGS" ]; then
  run_pylint "$@"
  exit
fi

GIT_LS_FILES_ARGS=("-om" "--exclude-standard")

while [[ $# -gt 0 ]]; do
  case "$1" in
    --jobs)
      JOBS="$2"
      shift 2
      ;;
    --path)
      GIT_LS_FILES_ARGS=("$2")
      shift 2
      ;;
    --rcfile)
      RCFILE="$2"
      shift 2
      ;;
    *)
      >&2 echo Unknown pylint arg: "$1"
      exit 1
      ;;
  esac
done

if [[ $(git ls-files "${GIT_LS_FILES_ARGS[@]}" | grep -c '\.py$') -ne 0 ]]; then
  git ls-files "${GIT_LS_FILES_ARGS[@]}" \
    | grep '\.py$' \
    | \
      _NO_PARSE_ARGS=x \
      JOBS="$JOBS" \
      RCFILE="$RCFILE" \
      xargs "$0"
fi
