#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

DEPCHECK_IGNORES="@aws-sdk/client-sso-oidc,@aws-sdk/client-sts,@babel/register,@fortawesome/fontawesome-free,buffer,lodash-es,minimist,process,webpack-cli"
UNUSED_DEPS="$(mktemp)"

yarn -s depcheck --version

set +e
yarn -s depcheck --ignores="$DEPCHECK_IGNORES" --json 2>/dev/null | jq .dependencies >"$UNUSED_DEPS"
set -e

if ! [ "$(cat "$UNUSED_DEPS")" = '[]' ]; then
  >&2 echo "Some dependencies are unused"
  >&2 cat "$UNUSED_DEPS"
  >&2 echo "Remove them, or add them as development dependencies with \`yarn add -D ...\`"
  exit 1
fi

echo "Found no unused dependencies"
