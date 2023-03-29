#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

exec gunicorn \
 --log-file - \
 --worker-class gevent \
 --limit-request-line 8190 \
 "$@"
