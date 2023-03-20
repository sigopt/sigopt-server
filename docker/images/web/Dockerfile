# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG BUILD_TAG=build
ARG NODE_VERSION


FROM sigopt/compile-web-client-side:${BUILD_TAG} AS client-artifacts
FROM sigopt/compile-web-server-side:${BUILD_TAG} AS server-artifacts


FROM node:${NODE_VERSION}-alpine

# hadolint ignore=DL3018
RUN set -ex \
  ; apk update \
  ; apk add --no-cache --upgrade apk-tools \
  ; apk upgrade --available \
  ; :

RUN set -ex \
  ; apk add --no-cache runuser~=2 \
  ; :

WORKDIR /sigopt-server

COPY config /sigopt-server/config
COPY web/js /sigopt-server/web/js
COPY web/scripts /sigopt-server/web/scripts

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
