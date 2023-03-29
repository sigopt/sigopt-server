#!/usr/bin/env bash
set -e
set -o pipefail

./scripts/launch/compose.sh run --rm \
  protowatch \
  ./tools/protobuf/compile.sh
