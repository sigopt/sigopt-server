#!/usr/bin/env bash
set -e
set -o pipefail

export NODE_DOMAIN=server
export NODE_OPTIONS="--max-old-space-size=2048"
exec yarn -s webpack \
  --config=web/js/webpack/client_side.config.babel.js \
  --env=NODE_ENV=production
