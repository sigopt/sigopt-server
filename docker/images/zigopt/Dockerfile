# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG BASE_IMAGE
ARG BUILD_TAG=build
ARG PYTHON_VERSION


# hadolint ignore=DL3006
FROM ${BASE_IMAGE} AS protobuf

ARG PROTOBUF_VERSION
COPY tools/protobuf/install.sh /install_protobuf.sh
RUN set -ex \
  ; /install_protobuf.sh "$PROTOBUF_VERSION" \
  ; :

WORKDIR /sigopt-server

COPY src/protobuf/zigopt/ /sigopt-server/src/protobuf/zigopt/
COPY tools/protobuf/compile.sh /compile_protobuf.sh
RUN : \
  ; /compile_protobuf.sh \
  ; :


FROM python:${PYTHON_VERSION}-alpine

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

COPY requirements.txt /sigopt-server/requirements.txt
RUN set -ex \
  ; pip install --no-cache-dir -r requirements.txt \
  ; :

COPY src/python/zigopt/ /sigopt-server/src/python/zigopt/
COPY --from=protobuf src/python/zigopt/ /sigopt-server/src/python/zigopt/

COPY sigoptcompute/sigoptcompute /sigopt-server/sigoptcompute/sigoptcompute
copy sigoptaux/sigoptaux /sigopt-server/sigoptaux/sigoptaux

ENV PYTHONPATH /sigopt-server/src/python:/sigopt-server/sigoptcompute:/sigopt-server/sigoptaux:/sigopt-server

RUN set -ex \
  ; python -c 'import zigopt.api.prod' \
  ; :

RUN set -ex \
  ; adduser -S produser \
  ; :

USER produser

COPY config /sigopt-server/config
COPY docker/images/zigopt/bin/ /usr/local/bin/
