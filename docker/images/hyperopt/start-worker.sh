#!/usr/bin/env bash
set -e
set -o pipefail

pushd /sigopt-python
pip install '.[dev]'
popd

hyperopt-mongo-worker --mongo=mongodb:27017/foo_db --poll-interval=0.1 --max-consecutive-failures=100000
