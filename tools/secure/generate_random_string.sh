#!/usr/bin/env bash
set -e
# no_pipefail

COUNT="${1:-48}"

tr --complement --delete '_A-Z-a-z-0-9~@#%^&*()+={}[]|:<>,./?' </dev/urandom | head -c"$COUNT"
