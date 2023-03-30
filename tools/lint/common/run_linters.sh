#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail


./tools/lint/common/check_copyright_and_license_disclaimers.py "$@" --fix-in-place
