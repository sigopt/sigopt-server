# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG BASE_IMAGE=debian:buster-slim
ARG BUILD_TAG=build


# hadolint ignore=DL3006
FROM ${BASE_IMAGE}

SHELL ["/bin/bash", "-exo", "pipefail", "-c"]

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get upgrade -yqq >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends \
      ca-certificates=* \
      curl=7.64.* \
      g++=4:8.3.* \
      git=1:2.20.* \
      libpython3-stdlib=3.7.* \
      make=4.2.* \
      python3-minimal=3.7.* \
      xz-utils=5.* \
      > /dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

COPY tools/node/install.sh /install_node.sh
ARG NODE_VERSION

RUN set -ex \
  ; /install_node.sh "$NODE_VERSION" \
  ; :

WORKDIR /sigopt-server

COPY package.json /sigopt-server/package.json
COPY yarn.lock /sigopt-server/yarn.lock

RUN set -ex \
  ; yarn install --silent \
  ; yarn cache clean \
  ; :

COPY .babelrc /sigopt-server/
