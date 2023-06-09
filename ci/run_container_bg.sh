#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

./ci/compose.sh build --progress=plain "$1"
./ci/compose.sh up -d "$@"
