# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG BUILD_TAG=build


FROM sigopt/python-development:${BUILD_TAG}

SHELL ["/bin/bash", "-exo", "pipefail", "-c"]

WORKDIR /sigopt-server

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends libgomp1=8.3.* >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

COPY src/protobuf/zigopt/ /sigopt-server/src/protobuf/zigopt/
COPY src/python/zigopt/ /sigopt-server/src/python/zigopt/

WORKDIR /sigopt-server

COPY tools/protobuf/compile.sh /compile_protobuf.sh
RUN : \
  ; /compile_protobuf.sh \
  ; :

COPY sigoptcompute/sigoptcompute /sigopt-server/sigoptcompute/sigoptcompute
copy sigoptaux/sigoptaux /sigopt-server/sigoptaux/sigoptaux

ENV PYTHONPATH /sigopt-server/src/python:/sigopt-server/sigoptcompute:/sigopt-server/sigoptaux:/sigopt-server

RUN set -ex \
  ; python -c 'import zigopt.api.prod' \
  ; :

RUN set -ex \
  ; useradd produser \
  ; :

USER produser

COPY config /sigopt-server/config
COPY docker/images/zigopt/bin/ /usr/local/bin/
