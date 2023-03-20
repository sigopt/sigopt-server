#!/usr/bin/env bash
set -e
set -o pipefail

mkdir -p artifacts/trivy
python ./docker/scan_application_images.py --registry=sigopt --tag=scan -- "$@"
