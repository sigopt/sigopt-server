#!/usr/bin/env bash
set -e
set -o pipefail

playwright codegen --target=python https://sigopt.ninja:4443 "$@"
