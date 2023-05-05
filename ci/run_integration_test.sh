#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail
set -x

function run_fg {
  ./ci/run_container_fg.sh "$@"
}

function run_bg {
  ./ci/run_container_bg.sh "$@"
}

TEST="$1"
shift

./ci/init_config.sh

run_bg postgres
run_fg createdb --fake-data
run_bg redis
run_bg minio
run_fg init-minio-cookiejar
run_fg init-minio-filestorage
run_bg smtp
for service in "$@"; do
  run_bg "$service"
done

./ci/compose.sh build --progress=plain test-runner
./ci/compose.sh run --rm test-runner \
  python test/test_runner.py \
    --config-dir config/circleci/ \
    --skip-compile \
    "$TEST"
