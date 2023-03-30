#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

# if you're playing around on a dev machine and just
# want to install the whole world

set -e
set -o pipefail

sudo deploys/common/apt/setup_instance.sh
pip install --upgrade pip
pip install --upgrade -r requirements.txt -r requirements-dev.txt
