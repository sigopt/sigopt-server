#!/usr/bin/env bash
set -e
set -o pipefail

FLAKE8_VERSION=$(flake8 --version)
if [[ ! $FLAKE8_VERSION = 3.* ]]; then
  >&2 echo 'Expected flake8 version3.x, but you have'
  >&2 echo "$FLAKE8_VERSION"
  >&2 echo 'First, pip uninstall flake8'
  >&2 echo 'Then pip install --upgrade flake8'
  exit 1
fi

git ls-files | grep '\.py$' | xargs ./pp flake8 --config=tools/lint/python/flake8.config "$@"
