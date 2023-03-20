#!/usr/bin/env bash
set -e
set -o pipefail


git submodule init && git submodule update

python3 docker/image_builder.py --build-tag=latest --threads=2 --clean-intermediate nginx node python
