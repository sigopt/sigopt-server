#!/usr/bin/env bash
set -e
set -o pipefail

bandit -c tools/lint/python/bandit.config.yaml "$@"
