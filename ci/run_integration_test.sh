#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail
set -x

function run_fg {
  ./ci/compose.sh build --progress=plain "$1"
  ./ci/compose.sh create "$1"
  ./ci/compose.sh run --rm "$@"
}

function run_bg {
  ./ci/compose.sh build --progress=plain "$1"
  ./ci/compose.sh up -d "$@"
}

TEST="$1"
shift

./ci/compose.sh run -Ti --rm init-config sh -e <<EOF
  cp /sigopt-server/config/circleci/* /etc/sigopt/server-config/
  echo CHANGEME123 >/etc/minio/password.txt
EOF

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
