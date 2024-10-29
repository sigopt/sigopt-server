# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG NODE_MAJOR


# hadolint ignore=DL3006
FROM node:${NODE_MAJOR}-bookworm

SHELL ["/bin/bash", "-exo", "pipefail", "-c"]

RUN set -ex \
  ; apt-get update -y >/dev/null \
  ; apt-get upgrade -y >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

# hadolint ignore=DL3016
RUN set -ex \
  ; npm install -g npm yarn --force \
  ; npm cache clean --force \
  ; :

RUN set -ex \
  ; apt-get update -y >/dev/null \
  ; apt-get install -y --no-install-recommends \
      ca-certificates=* \
      curl=7.* \
      g++=4:* \
      git=1:* \
      libpython3-stdlib=3.11.* \
      make=4.* \
      python3-minimal=3.11.* \
      xz-utils=5.* \
      > /dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

WORKDIR /sigopt-server

COPY package.json /sigopt-server/package.json
COPY yarn.lock /sigopt-server/yarn.lock

RUN set -ex \
  ; yarn install --silent \
  ; yarn cache clean \
  ; :

COPY .babelrc /sigopt-server/
