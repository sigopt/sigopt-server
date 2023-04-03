#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

SIGOPT_PYTHON_GIT_REFERENCE=${1:-'main'}
echo "sigopt-python: $SIGOPT_PYTHON_GIT_REFERENCE"

git clone https://github.com/sigopt/sigopt-python.git
cd sigopt-python
git fetch --all --tags --prune
git checkout "$SIGOPT_PYTHON_GIT_REFERENCE"
pip install '.[dev]'

apt-get update && apt-get -y install default-jre
hyperopt-mongo-worker --mongo=mongodb:27017/foo_db --poll-interval=0.1 --max-consecutive-failures=100000 &>/dev/null &
sleep 3

export SIGOPT_PROJECT=hyperopt-integration-test
env
sigopt create project
make integration_test
