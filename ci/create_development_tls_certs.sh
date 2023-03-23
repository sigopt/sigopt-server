#!/usr/bin/env bash
set -e
set -o pipefail

export EDITOR=true

./tools/tls/generate_root_ca.sh
./tools/tls/generate_san_cert.sh
