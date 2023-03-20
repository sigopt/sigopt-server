#!/usr/bin/env bash
set -e
set -o pipefail

MIN_VERSION="3.12"
MAX_VERSION="3.99"

set +e
CURRENT_VERSION="$(protoc --version | sed 's/libprotoc //')"
set -e

CLAMPED_MIN_VERSION="$(printf "%s\\n%s\\n" "$MIN_VERSION" "$CURRENT_VERSION" | sort --version-sort | head -n 1)"
CLAMPED_MAX_VERSION="$(printf "%s\\n%s\\n" "$MAX_VERSION" "$CURRENT_VERSION" | sort --version-sort | tail -n 1)"

if [[ "$CLAMPED_MIN_VERSION" != "$MIN_VERSION" || "$CLAMPED_MAX_VERSION" != "$MAX_VERSION" ]]; then
  >&2 echo "Expected protoc version between \`v$MIN_VERSION\` and \`v$MAX_VERSION\`, and you have \`v$CURRENT_VERSION\`"
  >&2 echo
  >&2 echo "On Mac, run \`brew install protobuf\`"
  exit 1
fi

find src/protobuf/zigopt/protobuf/gen -name '*.proto' -print0 | xargs -0 \
  protoc \
  -I=src/protobuf \
  -I=/usr/local/include \
  --python_out=src/python

find src/python/zigopt/protobuf/gen -name '*.py' | while read -r file; do
  sed -i'.protobak' '1s/^/# type: ignore\n/' "$file"
  rm "$file.protobak"
done
