#!/usr/bin/env bash
set -e
set -o pipefail


./tools/lint/common/eof_lint.sh
./tools/lint/common/check_copyright_and_license_disclaimers.py "$@" --fix-in-place
