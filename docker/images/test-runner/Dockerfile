# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
FROM ubuntu:jammy-20230308

SHELL ["/bin/bash", "-exo", "pipefail", "-c"]

ENV DEBIAN_FRONTEND noninteractive

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get upgrade -yqq >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :
