# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG NODE_MAJOR


FROM node:${NODE_MAJOR}-alpine AS node-base

# hadolint ignore=DL3018
RUN set -ex \
  ; apk update \
  ; apk add --no-cache --upgrade apk-tools \
  ; apk upgrade --available \
  ; :

RUN set -ex \
  ; npm update -g \
  ; :

WORKDIR /sigopt-server


FROM node-base AS node-modules

# hadolint ignore=DL3016
RUN set -ex \
  ; npm install -g npm yarn --force \
  ; npm cache clean --force \
  ; :

COPY package.json /sigopt-server/package.json
RUN set -ex \
  ; yarn install --production --silent \
  ; yarn cache clean \
  ; :


FROM node-modules AS node-build

COPY .babelrc /sigopt-server/
COPY web /sigopt-server/web


FROM node-modules AS client-artifacts

COPY scripts/compile/minify_js.sh /sigopt-server/scripts/compile/minify_js.sh

RUN ./scripts/compile/minify_js.sh


FROM node-modules AS server-artifacts

COPY scripts/compile/minify_js_server_bundle.sh /sigopt-server/scripts/compile/minify_js_server_bundle.sh

RUN ./scripts/compile/minify_js_server_bundle.sh


FROM node-base

RUN set -ex \
  ; apk add --no-cache runuser~=2 \
  ; :

COPY --from=node-modules /sigopt-server/node_modules/ /sigopt-server/node_modules/
COPY --from=client-artifacts /sigopt-server/artifacts/web/ /sigopt-server/artifacts/web/
COPY --from=server-artifacts /sigopt-server/artifacts/web/ /sigopt-server/artifacts/web/

RUN set -ex \
  ; adduser -S produser \
  ; :

EXPOSE 4000

ENV NODE_DOMAIN server
ENV NODE_ENV production

ENTRYPOINT ["/usr/bin/env", "runuser", "-u", "produser", "--"]

CMD ["node", "artifacts/web/server/server.js", "/sigopt-server", "--workers", "1"]
