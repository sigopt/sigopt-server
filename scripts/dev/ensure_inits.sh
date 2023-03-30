#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

DIR="$1"

find "$DIR" -not -name __pycache__ -type d -exec touch {}/__init__.py \;
