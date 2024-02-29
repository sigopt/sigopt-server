# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG NGINX_VERSION


FROM nginx:${NGINX_VERSION}-alpine-slim

RUN set -ex \
  ; apk update \
  ; apk upgrade --available \
  ; :

COPY nginx/ /etc/nginx/

RUN mkdir -p /var/run/nginx

ENTRYPOINT []

CMD ["nginx", "-g", "daemon off;"]
