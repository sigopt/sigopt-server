#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

pushd /sigopt-python
pip install '.[dev]'
popd

hyperopt-mongo-worker --mongo=mongodb:27017/foo_db --poll-interval=0.1 --max-consecutive-failures=100000
