# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG BUILD_TAG=build
ARG NODE_VERSION


FROM node:${NODE_VERSION} AS node-build

# hadolint ignore=DL3016
RUN set -ex \
  ; npm update -g \
  ; npm install -g npm yarn --force \
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


FROM node-build AS client-artifacts

COPY scripts/compile/minify_js /sigopt-server/scripts/compile/minify_js

RUN ./scripts/compile/minify_js


FROM node-build AS server-artifacts

COPY scripts/compile/minify_js_server_bundle /sigopt-server/scripts/compile/minify_js_server_bundle

RUN ./scripts/compile/minify_js_server_bundle


FROM node:${NODE_VERSION}-alpine

# hadolint ignore=DL3018
RUN set -ex \
  ; apk update \
  ; apk add --no-cache --upgrade apk-tools \
  ; apk upgrade --available \
  ; :

RUN set -ex \
  ; npm update -g \
  ; :

RUN set -ex \
  ; apk add --no-cache runuser~=2 \
  ; :

WORKDIR /sigopt-server

COPY --from=client-artifacts /sigopt-server/artifacts/web/ /sigopt-server/artifacts/web/
COPY --from=server-artifacts /sigopt-server/artifacts/web/ /sigopt-server/artifacts/web/

COPY config /sigopt-server/config

RUN set -ex \
  ; adduser -S produser \
  ; :

EXPOSE 4000

ENV NODE_DOMAIN server
ENV NODE_ENV production

ENTRYPOINT ["/usr/bin/env", "runuser", "-u", "produser", "--"]

CMD ["node", "artifacts/web/server/server.js", "/sigopt-server", "--workers", "1"]
