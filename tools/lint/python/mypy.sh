#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

exec ./pp mypy -p zigopt.common -p zigopt.config -p zigopt.handlers.validate -p zigopt.json -p zigopt.protobuf
