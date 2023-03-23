#!/usr/bin/env bash
set -e
set -o pipefail

DIR="$1"

find "$DIR" -not -name __pycache__ -type d -exec touch {}/__init__.py \;
