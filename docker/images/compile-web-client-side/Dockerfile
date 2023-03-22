# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG NODE_VERSION


FROM node:${NODE_VERSION}

ARG NPM_VERSION
ARG YARN_VERSION
RUN set -ex \
  ; npm install -g "npm@$NPM_VERSION" "yarn@$YARN_VERSION" --force \
  ; npm cache clean --force \
  ; :

WORKDIR /sigopt-server

COPY package.json /sigopt-server/package.json
RUN set -ex \
  ; yarn install --production --silent \
  ; yarn cache clean \
  ; :

COPY .babelrc /sigopt-server/
COPY config /sigopt-server/config
COPY web /sigopt-server/web

COPY scripts/compile/minify_js.sh /sigopt-server/scripts/compile/minify_js.sh

RUN ./scripts/compile/minify_js.sh
