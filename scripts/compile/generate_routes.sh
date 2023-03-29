#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

CONFIG_FILE="${1:?Missing config file as first argument}"

echo "Generating route manifest for tests"
yarn -s webpack --config=./webpack.config.script.babel.js --env=SCRIPT=./web/scripts/generate_routes.js
sigopt_server_config_file="$CONFIG_FILE" node artifacts/js_script/generate_routes.js
