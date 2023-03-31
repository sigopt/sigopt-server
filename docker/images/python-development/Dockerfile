# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG PYTHON_MAJOR
ARG PYTHON_MINOR


# hadolint ignore=DL3006
FROM python:${PYTHON_MAJOR}.${PYTHON_MINOR}-buster

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get upgrade -yqq >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      ca-certificates=* \
      curl=7.64.* \
      procps=2:3.3.* \
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

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      gcc=4:8.3.* \
      git=1:2.20.* \
      libc6-dev=2.* \
      libssl-dev=1.1.* \
      libxml2-dev=2.9.* \
      libxml2=2.9.* \
      make=4.2.* \
      pkg-config=0.29-* \
      sqlite3=3.27.* \
      >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

COPY Pipfile.lock /sigopt-server/Pipfile.lock

RUN set -ex \
  ; pip install --upgrade --no-cache-dir "pipenv>=2023.3.20" \
  ; pipenv install --dev --ignore-pipfile \
  ; pipenv --clear \
  ; :

ENV PATH "/sigopt-server/.venv/bin:$PATH"

RUN set -ex \
  ; python -c 'import inotify, lxml, numpy' \
  ; :

COPY docker/images/python-development/bin /usr/local/bin

ENV OMP_NUM_THREADS 1
ENV OPENBLAS_NUM_THREADS 1
ENV MKL_NUM_THREADS 1
ENV VECLIB_MAXIMUM_THREADS 1
ENV NUMEXPR_NUM_THREADS 1

CMD ["/usr/local/bin/python3"]
