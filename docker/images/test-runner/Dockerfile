# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG BUILD_TAG=build


FROM ubuntu:focal-20221130

SHELL ["/bin/bash", "-exo", "pipefail", "-c"]

ENV DEBIAN_FRONTEND noninteractive

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get upgrade -yqq >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

RUN : \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      build-essential=12.* \
      ca-certificates=* \
      curl=7.* \
      git=1:2.* \
      libbz2-dev=1.0.* \
      libc-bin=2.* \
      libc6=2.* \
      libexpat1-dev=2.2.* \
      libffi-dev=3.* \
      libgdbm-dev=1.18.* \
      libgomp1=10.* \
      liblzma-dev=5.2.* \
      libncursesw5-dev=6.* \
      libreadline-dev=8.* \
      libsqlite3-dev=3.* \
      libssl-dev=1.1.* \
      libssl1.1=1.1.* \
      libxml2=2.9.* \
      lxde=10  \
      make=4.2.* \
      netbase=6.* \
      pkg-config=0.29* \
      sqlite3=3.* \
      unzip=6.* \
      uuid-dev=2.* \
      x11vnc=0.9.* \
      xvfb=2:1.20.* \
      xz-utils=5.2.* \
      zlib1g-dev=1:1.2.* \
      >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

ARG PROTOBUF_VERSION
COPY tools/protobuf/install.sh /install_protobuf.sh
RUN set -ex \
  ; /install_protobuf.sh "$PROTOBUF_VERSION" \
  ; :

ARG PYTHON_VERSION
ENV PYTHON_TAR_URL "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"
RUN : \
  ; curl -fSsL "$PYTHON_TAR_URL" | tar -xzf - --strip-components=1 \
  ; ./configure --with-ensurepip=install >/dev/null \
  ; make CFLAGS="-w" --silent --jobs=4 install >/dev/null \
  ; ln -s python3 /usr/local/bin/python \
  ; ln -s pip3 /usr/local/bin/pip \
  ; ldconfig \
  ; python --version \
  ; pip --version \
  ; :

WORKDIR /sigopt-server

COPY requirements.txt /sigopt-server/requirements.txt
COPY requirements-dev.txt /sigopt-server/requirements-dev.txt
RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      build-essential=12.* \
      libxml2-dev=2.9.* \
      >/dev/null \
  ; apt-mark auto build-essential libxml2-dev libxmlsec1-dev \
  ; pip install --no-cache-dir --upgrade -r requirements.txt -r requirements-dev.txt \
  ; apt-get autoremove -yqq \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

RUN set -ex \
  ; python -c 'import lxml' \
  ; :

COPY src/protobuf/zigopt /sigopt-server/src/protobuf/zigopt
COPY src/python/zigopt /sigopt-server/src/python/zigopt
COPY tools/protobuf/compile.sh /compile_protobuf.sh
RUN : \
  ; /compile_protobuf.sh \
  ; :

COPY sigoptcompute/sigoptcompute /sigopt-server/sigoptcompute/sigoptcompute
COPY sigoptaux/sigoptaux /sigopt-server/sigoptaux/sigoptaux

ENV PYTHONPATH /sigopt-server/src/python:/sigopt-server/sigoptcompute:/sigopt-server/sigoptaux:/sigopt-server

RUN set -ex \
  ; python -c 'import zigopt.api.prod' \
  ; :

COPY ci /sigopt-server/ci
COPY config /sigopt-server/config
COPY pytest.ini /sigopt-server/pytest.ini
COPY scripts /sigopt-server/scripts
COPY test /sigopt-server/test
COPY web /sigopt-server/web

ENV PYTHONPATH /sigopt-server/src/python:/sigopt-server/test/python:/sigopt-server/test:/sigopt-server/sigoptcompute:/sigopt-server/sigoptaux:/sigopt-server

RUN set -ex \
  ; mkdir -p \
      failure_console_logs \
      screenshots/failure \
  ; :

ENV OMP_NUM_THREADS 1
ENV OPENBLAS_NUM_THREADS 1
ENV MKL_NUM_THREADS 1
ENV VECLIB_MAXIMUM_THREADS 1
ENV NUMEXPR_NUM_THREADS 1
