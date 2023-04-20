#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

CONFIG_DIR="${1:?Missing config dir as first argument}"

echo "Generating route manifest for tests"
yarn -s webpack --config=./webpack.config.script.babel.js --env=SCRIPT=./web/scripts/generate_routes.js
SIGOPT_SERVER_CONFIG_DIR="$CONFIG_DIR" node artifacts/js_script/generate_routes.js
