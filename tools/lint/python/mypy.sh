#!/usr/bin/env bash
set -e
set -o pipefail

exec ./pp mypy -p zigopt.common -p zigopt.config -p zigopt.handlers.validate -p zigopt.json -p zigopt.protobuf
