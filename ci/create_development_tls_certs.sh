#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

export EDITOR=true

./tools/tls/generate_root_ca.sh
./tools/tls/generate_san_cert.sh
