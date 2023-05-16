#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

PROTOBUF_VERSION="3.19.6"
PROTOBUF_ZIP_URL="https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOBUF_VERSION}/protoc-${PROTOBUF_VERSION}-linux-x86_64.zip"

TEMPDIR="$(mktemp -d)"
(
  cd "$TEMPDIR"
  curl -fSsL "$PROTOBUF_ZIP_URL" >protoc.zip
  unzip protoc.zip
  install ./bin/protoc /usr/local/bin/protoc
  chmod a+rx -R ./include
  cp -Rp ./include/* /usr/local/include
)
rm -r "$TEMPDIR"
