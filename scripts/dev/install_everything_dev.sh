#!/usr/bin/env bash

# if you're playing around on a dev machine and just
# want to install the whole world

set -e
set -o pipefail

sudo deploys/common/apt/setup_instance.sh
pip install --upgrade pip
pip install --upgrade -r requirements.txt -r requirements-dev.txt
