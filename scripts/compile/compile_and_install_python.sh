#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

PYTHON_DIR=$(mktemp -d)

source .env
PYTHON_VERSION="${PYTHON_MAJOR}.${PYTHON_MINOR}.${PYTHON_PATCH}"

JOBS=4
while [[ $# -gt 0 ]]
do
  case "$1" in
    --jobs) JOBS="${2:?Missing argument for --jobs}"; shift 2 ;;
    --version) PYTHON_VERSION="${2:?Missing argument for --version}"; shift 2 ;;
    --with-pip) WITH_PIP="--with-ensurepip=install" ; shift ;;
    *) echo Unknown arg: "$1"; exit 1 ;;
  esac
done

PYTHON_TAR_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"

(
  cd "$PYTHON_DIR"
  echo "Downloading $PYTHON_TAR_URL"
  curl -fsSL "${PYTHON_TAR_URL}" | tar xzf - --strip-components=1 --no-same-owner
  echo "Building Python $PYTHON_VERSION"
  ./configure "$WITH_PIP"
  make CFLAGS="-w" --silent --jobs="$JOBS"
  make install
)
