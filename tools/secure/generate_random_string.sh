#!/usr/bin/env bash
set -e
# no_pipefail

COUNT="${1:-48}"

docker pull --quiet busybox >/dev/null
docker run -i --rm busybox sh <<EOF
tr -cd 'A-Za-z0-9_-~@#%^&*()+={}[]|:<>,./?' </dev/urandom | head -c"$COUNT"
EOF
