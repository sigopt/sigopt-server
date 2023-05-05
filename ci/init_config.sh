#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

./ci/compose.sh run -Ti --rm init-config sh -e <<EOF
  cp /sigopt-server/config/circleci/* /etc/sigopt/server-config/
  echo CHANGEME123 >/etc/minio/password.txt
EOF
