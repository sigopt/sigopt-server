#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail
. scripts/launch/setup_env.sh
./scripts/launch/compose.sh stop "${PERSISTENT_SERVICES[@]}"
