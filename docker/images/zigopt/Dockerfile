# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG PYTHON_MAJOR
ARG PYTHON_MINOR


# hadolint ignore=DL3006
FROM debian:bookworm AS protobuf

RUN set -ex \
  ; apt-get update -y >/dev/null \
  ; apt-get install -y --no-install-recommends --no-install-suggests \
      ca-certificates=* \
      curl=* \
      unzip=* \
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


FROM python:${PYTHON_MAJOR}.${PYTHON_MINOR}-slim-bookworm

RUN set -ex \
  ; apt-get update -y >dev/null \
  ; apt-get upgrade -y >/dev/null \
  ; apt-get install -y --no-install-recommends --no-install-suggests \
      gcc=* \
      git=* \
      libstdc++-11-dev=* \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

# hadolint ignore=DL3013
RUN set -ex \
  ; pip install --upgrade --no-cache-dir pip setuptools wheel \
  ; :

WORKDIR /sigopt-server

COPY Pipfile.lock /sigopt-server/Pipfile.lock
ENV PIPENV_VENV_IN_PROJECT "1"
RUN set -ex \
  ; pip install --upgrade --no-cache-dir "pipenv>=2023.3.20" \
  ; pipenv sync\
  ; pipenv --clear \
  ; :

ENV PATH "/sigopt-server/.venv/bin:$PATH"

COPY src/python/zigopt/ /sigopt-server/src/python/zigopt/
COPY --from=protobuf /sigopt-server/src/python/zigopt/ /sigopt-server/src/python/zigopt/

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
