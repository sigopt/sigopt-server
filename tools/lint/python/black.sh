#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

black --config=tools/lint/python/pyproject.toml --experimental-string-processing "$@"
