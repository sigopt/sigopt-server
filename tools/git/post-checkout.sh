#!/usr/bin/env bash
set -e
set -o pipefail

TYPE="$3"
if [ "$TYPE" != "1" ]; then
  # This is a file checkout
  exit
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if ! [[ "$BRANCH" =~ ^[0-9a-zA-Z./_-]+$ ]]; then
  >&2 echo "WARNING: This branch has some characters that might not be handled appropriately. Consider renaming to something that has only numbers, letters, '/', '.', '_' and '-'."
fi
