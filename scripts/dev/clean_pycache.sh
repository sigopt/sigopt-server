#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

find "$@" -name __pycache__ -depth -type d -exec rm -rf \{\} \;
