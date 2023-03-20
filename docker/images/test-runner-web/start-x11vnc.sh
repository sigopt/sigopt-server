#!/usr/bin/env bash
set -e
set -o pipefail

for _ in {1..30}; do
  if x11vnc -forever -shared -quiet -geometry "$GEOMETRY" -display "$DISPLAY" >/dev/null; then
    break
  fi
  sleep 1
done
