#!/usr/bin/env bash

# no_set_e
set -o pipefail

API_DIR=$("$1/scripts/readlink.py" "$1")

PYTHONPATH="$PYTHONPATH:$API_DIR/src/python"
PYTHONPATH="$PYTHONPATH:$API_DIR/test/python"
PYTHONPATH="$PYTHONPATH:$API_DIR/test"
PYTHONPATH="$PYTHONPATH:$API_DIR"
export PYTHONPATH
