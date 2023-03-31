#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

TYPE="$1"
shift
RESOURCE="$1"
shift

# shellcheck disable=SC2317
function file {
  [ -f "$RESOURCE" ]
}

# shellcheck disable=SC2317
function url {
  curl -fL --cacert artifacts/tls/root-ca.crt "$@" "$RESOURCE"
}

TRIES=72
WAIT_SECONDS=5

for (( i=1; i<=TRIES; i++ )); do
  if "$TYPE" "$@"; then
    exit
  fi
  sleep "$WAIT_SECONDS"
done

>&2 echo "Timed out waiting for $RESOURCE"
exit 1
