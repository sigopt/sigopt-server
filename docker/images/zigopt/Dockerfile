# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG PYTHON_MAJOR
ARG PYTHON_MINOR


# hadolint ignore=DL3006
FROM debian:buster AS protobuf

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      ca-certificates=* \
      curl=7.64.* \
      unzip=6.* \
      >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

ARG PROTOBUF_VERSION
COPY tools/protobuf/install.sh /install_protobuf.sh
RUN set -ex \
  ; /install_protobuf.sh "$PROTOBUF_VERSION" \
  ; :

WORKDIR /sigopt-server

COPY src/protobuf/zigopt/ /sigopt-server/src/protobuf/zigopt/
COPY tools/protobuf/compile.sh /compile_protobuf.sh
RUN set -ex \
  ; /compile_protobuf.sh \
  ; :


FROM python:${PYTHON_MAJOR}.${PYTHON_MINOR}-buster

RUN set -ex \
  ; apt-get update -yqq >dev/null \
  ; apt-get upgrade -yqq >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

# hadolint ignore=DL3013
RUN set -ex \
  ; pip install --upgrade --no-cache-dir pip setuptools wheel \
  ; :

WORKDIR /sigopt-server

COPY requirements.txt /sigopt-server/requirements.txt
RUN set -ex \
  ; pip install --no-cache-dir -r requirements.txt \
  ; :

COPY src/python/zigopt/ /sigopt-server/src/python/zigopt/
COPY --from=protobuf /sigopt-server/src/python/zigopt/ /sigopt-server/src/python/zigopt/

COPY libsigopt /sigopt-server/libsigopt

ENV PYTHONPATH /sigopt-server/src/python:/sigopt-server

RUN set -ex \
  ; python -c 'import zigopt.api.prod' \
  ; :

RUN set -ex \
  ; useradd produser \
  ; :

USER produser

ENV OMP_NUM_THREADS 1
ENV OPENBLAS_NUM_THREADS 1
ENV MKL_NUM_THREADS 1
ENV VECLIB_MAXIMUM_THREADS 1
ENV NUMEXPR_NUM_THREADS 1

COPY docker/images/zigopt/bin/ /usr/local/bin/
