#!/usr/bin/env bash
set -e
set -o pipefail

NODE_VERSION="${1:?Missing node version as first argument}"

ARCH=x64
NODE_TAR_URL="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${ARCH}.tar.xz"
(
  cd /usr/local
  curl -fSsL "$NODE_TAR_URL" | tar -xJf - --strip-components=1
  ldconfig
  node --version
  npm install -g npm yarn
  npm cache clean --force
)
