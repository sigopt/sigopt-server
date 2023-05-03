#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

function run_fg {
  ./ci/compose.sh build --progress=plain "$1"
  ./ci/compose run --rm "$@"
}

function run_bg {
  ./ci/compose.sh build --progress=plain "$1"
  ./ci/compose run -d "$@" &
}

TEST="$1"
shift

run_bg postgres
run_fg createdb --fake-data
run_bg redis
run_bg minio
run_fg init-minio-cookiejar
run_fg init-minio-filestorage
for service in "$@"; do
  run_bg "$service"
done

./ci/compose.sh build --progress=plain test-runner
./ci/compose.sh run --rm test-runner \
  python test/test_runner.py \
    --config-dir config/circleci/ \
    --skip-compile \
    "$TEST"