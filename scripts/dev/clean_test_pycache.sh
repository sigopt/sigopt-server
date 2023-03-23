#!/usr/bin/env bash
set -e
set -o pipefail

exec ./scripts/dev/clean_pycache.sh sigoptcompute/testcompute test
