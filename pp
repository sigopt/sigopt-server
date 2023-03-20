#!/usr/bin/env bash

# Use this file to run your commands with PYTHONPATH appropriately set.
# For example, instead of running
#    PYTHONPATH=/a/bunch/of:/long/paths yourcommand
# you can just run
#    ./pp yourcommand
# and the PYTHONPATH will be set appropriately, including the relevant
# sigopt-server code.

set -e
set -o pipefail
DIR=$( dirname "${BASH_SOURCE[0]}" )
source "$DIR/scripts/set_python_path" "$DIR"
exec -- "$@"
