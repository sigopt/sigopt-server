#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

source .env

docker run -i --rm \
  --volume="$(pwd):/sigopt-server" \
  "python:${PYTHON_MAJOR}.${PYTHON_MINOR}-buster" \
  bash -eo pipefail \
  <<EOF
apt-get update -yqq
apt-get install -yqq build-essential
python -mvenv /tmp/venv
source /tmp/venv/bin/activate
pip install --no-cache-dir --upgrade -r /sigopt-server/requirements-to-freeze.txt
pip freeze | sed --expression='/^-e \\/usr\\/local\\/lib\\/python.*\\/site-packages$/d' --expression='s/^.*(qmcpy==\\(.*\\))$/qmcpy==\\1/g' >/sigopt-server/requirements.txt
EOF

# sort the lines and add a comment
_tmp="$(mktemp)"
sort --ignore-case requirements.txt | grep -v site-packages >>"$_tmp"
echo '# auto-generated from scripts/requirements/freeze_requirements.sh' >requirements.txt
cat "$_tmp" >>requirements.txt
rm "$_tmp"

echo "Please commit changes to requirements.txt, rebuild images and restart your development environment to use the new modules"
