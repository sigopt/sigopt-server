# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
FROM ubuntu:22.04

COPY Dockerfile /Dockerfile

RUN set -ex \
  ; apt-get update -yqq \
  ; apt-get install --no-install-recommends -yqq lxde=11 \
  ; rm -rf /var/lib/apt/lists/* \
  ; :
