#!/usr/bin/env bash
# This script checks and fixes the sorting of object properties.
# It should not be executed directly.

set -e
set -o pipefail

function check {
  EXIT=0
  for FILE in "$@"; do
    SORTED_OUT="$(mktemp)"

    if ! python -mjson.tool "$FILE" >/dev/null; then
      >&2 echo "Invalid JSON syntax in $FILE"
      EXIT=1
    fi

    if ! diff <(python -mjson.tool --indent=2 "$FILE") <(python -mjson.tool --indent=2 --sort-keys "$FILE"); then
      >&2 echo "JSON keys not sorted in $FILE"
      EXIT=1
    fi

    if ! diff "$FILE" <(python -mjson.tool --indent=2 --sort-keys "$FILE"); then
      >&2 echo "Incorrect JSON whitespace in $FILE"
      EXIT=1
    fi
  done
  return "$EXIT"
}

function fix {
  EXIT=0
  for FILE in "$@"; do
    SORTED_OUT="$(mktemp)"
    if python -mjson.tool --indent=2 --sort-keys "$FILE" >"$SORTED_OUT"; then
      cat "$SORTED_OUT" >"$FILE"
    else
      EXIT=1
    fi
  done
  return "$EXIT"
}

function main {
  FILES=()
  CHECK=false
  FIX=false

  while [ $# -gt 0 ]; do
    case "$1" in
      --check) CHECK=true; shift;;
      --fix) FIX=true; shift;;
      *) FILES+=("$1"); shift;;
    esac
  done

  if [ ${#FILES[@]} -eq 0 ]; then
    while read -r FILE; do
      FILES+=("$FILE")
    done <<<"$(git ls-files '*.json')"
  fi

  if "$CHECK" || "$FIX"; then
    if "$CHECK"; then
      check "${FILES[@]}"
    fi
    if "$FIX"; then
      fix "${FILES[@]}"
    fi
  else
    >&2 echo "Missing --fix or --check"
    exit 1
  fi
}

main "$@"
