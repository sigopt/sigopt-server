#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

PYLINT_ARGS=()
ISORT_ARGS=()
JOBS_ARGS=()

while [ "$#" -ne 0 ]; do
  arg="$1"
  if [ -z "$ARG_GROUP" ] && [[ "$arg" == "--jobs" ]]; then
    JOBS_ARGS=( --jobs "$2" )
    shift 2
    continue
  fi
  if [[ "$arg" == "--pylint-args" ]]; then ARG_GROUP="pylint"; shift; continue; fi
  if [[ "$arg" == "--isort-args" ]]; then ARG_GROUP="isort"; shift; continue; fi

  if [[ "${ARG_GROUP}" == "pylint" ]]; then PYLINT_ARGS+=("$arg")
  elif [[ "${ARG_GROUP}" == "isort" ]]; then ISORT_ARGS+=("$arg")
  else
    >&2 echo Argument "${arg}" has unknown group!
    exit 1
  fi
  shift
done

./tools/lint/python/isort_lint.sh "${ISORT_ARGS[@]}" "${JOBS_ARGS[@]}"
./tools/lint/python/flake8.sh "${JOBS_ARGS[@]}"
./tools/lint/python/flake8_print.sh "${JOBS_ARGS[@]}"
./tools/lint/python/pylint.sh "${PYLINT_ARGS[@]}" "${JOBS_ARGS[@]}"
./tools/lint/python/custom_lint.sh
