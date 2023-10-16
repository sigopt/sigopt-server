# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG NODE_MAJOR


# hadolint ignore=DL3006
FROM node:${NODE_MAJOR}-buster

SHELL ["/bin/bash", "-exo", "pipefail", "-c"]

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get upgrade -yqq >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

# hadolint ignore=DL3016
RUN set -ex \
  ; npm install -g npm yarn --force \
  ; npm cache clean --force \
  ; :

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends \
      ca-certificates=* \
      curl=7.* \
      g++=4:* \
      git=1:* \
      libpython3-stdlib=3.7.* \
      make=4.* \
      python3-minimal=3.7.* \
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
