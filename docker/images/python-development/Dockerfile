# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG BASE_IMAGE=debian:buster-slim
ARG BUILD_TAG=build


# hadolint ignore=DL3006
FROM ${BASE_IMAGE} AS python-compile

SHELL ["/bin/bash", "-exo", "pipefail", "-c"]

ARG PYTHON_VERSION

ENV PYTHON_TAR_URL "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"

# hadolint ignore=DL3002
USER root
WORKDIR /src/python

RUN : \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      build-essential=12.* \
      ca-certificates=* \
      curl=7.64.* \
      libbz2-dev=1.0.* \
      libexpat1-dev=2.2.* \
      libffi-dev=3.2.* \
      libgdbm-dev=1.18.* \
      liblzma-dev=5.2.* \
      libncursesw5-dev=6.* \
      libreadline-dev=7.* \
      libsqlite3-dev=3.27.* \
      libssl-dev=1.1.* \
      pkg-config=0.29-* \
      uuid-dev=2.33.* \
      xz-utils=5.2.* \
      zlib1g-dev=1:1.2.* \
      >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

RUN : \
  ; curl -fSsL "$PYTHON_TAR_URL" | tar -xzf - --strip-components=1 \
  ; ./configure --with-ensurepip=install >/dev/null \
  ; make CFLAGS="-w" DESTDIR=/build --silent --jobs=4 install >/dev/null \
  ; ln -s python3.10 /build/usr/local/bin/python \
  ; ln -s pip3.10 /build/usr/local/bin/pip \
  ; find /build/usr/local -depth -type d -a \
      \( -name __pycache__  -o -name test -o -name tests \) \
      -exec rm -rf '{}' \; \
  ; :

RUN : \
  ; \cp -r /build/usr/local/ /usr/ \
  ; ldconfig \
  ; /usr/local/bin/pip install --quiet --no-cache-dir --root=/build --upgrade pip setuptools wheel \
  ; find /build/usr/local -depth -type d -a \
      \( -name __pycache__  -o -name test -o -name tests \) \
      -exec rm -rf '{}' \; \
  ; :


# hadolint ignore=DL3006
FROM ${BASE_IMAGE}

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get upgrade -yqq >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

ENV PATH /usr/local/bin:$PATH

ENV LANG C.UTF-8

WORKDIR /
# hadolint ignore=DL3002
USER root

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

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      ca-certificates=* \
      libc-bin=2.* \
      libc6=2.* \
      libgomp1=8.3.* \
      libssl1.1=1.1.* \
      libxml2=2.9.* \
      netbase=5.* \
      >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

COPY --from=python-compile /build/ /

RUN set -ex \
  ; ldconfig \
  ; python --version \
  ; :

WORKDIR /sigopt-server

COPY requirements.txt /sigopt-server/requirements.txt
RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      gcc=4:8.3.* \
      libc6-dev=2.* \
      libssl-dev=1.1.* \
      >/dev/null \
  ; apt-mark auto gcc libc6-dev libssl-dev \
  ; pip install --no-cache-dir --upgrade \
      -r requirements.txt \
      cryptography \
  ; apt-get autoremove -yqq >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

ENV DEVELOPMENT_RUNTIME_PACKAGES " \
"

# hadolint ignore=DL3008
RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      make=4.2.* \
      libxml2=2.9.* \
      shellcheck=0.5.* \
      sqlite3=3.27.* \
      git=1:2.20.* \
      >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

COPY requirements-dev.txt /sigopt-server/requirements-dev.txt
COPY requirements-linux.txt /sigopt-server/requirements-linux.txt
RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      gcc=4:8.3.* \
      libxml2-dev=2.9.* \
      pkg-config=0.29-* \
      >/dev/null \
  ; apt-mark auto gcc libxml2-dev pkg-config \
  ; pip install --no-cache-dir --upgrade -r requirements-dev.txt -r requirements-linux.txt \
  ; apt-get autoremove -yqq >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

RUN set -ex \
  ; python -c 'import lxml' \
  ; :

COPY docker/images/python-development/bin /usr/local/bin

ENV OMP_NUM_THREADS 1
ENV OPENBLAS_NUM_THREADS 1
ENV MKL_NUM_THREADS 1
ENV VECLIB_MAXIMUM_THREADS 1
ENV NUMEXPR_NUM_THREADS 1

CMD ["/usr/local/bin/python3.10.7"]
