#!/usr/bin/env bash
set -e
# no_pipefail

COUNT="${1:-48}"

tr --complement --delete 'A-Za-z0-9_-~@#%^&*()+={}[]|:<>,./?' </dev/urandom | head -c"$COUNT"
