#!/usr/bin/env bash
set -e
set -o pipefail

./node_modules/.bin/eslint web/js web/scripts "$@"
