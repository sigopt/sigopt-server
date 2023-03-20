#!/usr/bin/env bash
set -e
set -o pipefail

exec ./pp ./tools/lint/common/eof_lint.py
