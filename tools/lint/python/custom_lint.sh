#!/usr/bin/env bash
set -e
set -o pipefail

./pp ./tools/lint/python/custom_lint.py
