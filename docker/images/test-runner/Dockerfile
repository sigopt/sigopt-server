# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG NODE_MAJOR
ARG PYTHON_MAJOR
ARG PYTHON_MINOR


FROM node:${NODE_MAJOR} AS test-routes

# hadolint ignore=DL3016
RUN set -ex \
  ; npm install -g npm yarn --force \
  ; rm -rf /root/.npm \
  ; npm cache clean --force \
  ; :

WORKDIR /sigopt-server

COPY package.json /sigopt-server/package.json
COPY yarn.lock /sigopt-server/yarn.lock

RUN set -ex \
  ; yarn install --production --silent \
  ; yarn cache clean \
  ; :

COPY web /sigopt-server/web
COPY config/defaults.json /sigopt-server/config/defaults.json
COPY scripts/compile/generate_routes.sh /sigopt-server/scripts/compile/generate_routes.sh
COPY .babelrc /sigopt-server/.babelrc
COPY webpack.config.script.babel.js /sigopt-server/webpack.config.script.babel.js

RUN ./scripts/compile/generate_routes.sh config/


# hadolint ignore=DL3006
FROM python:${PYTHON_MAJOR}.${PYTHON_MINOR}-buster AS test-runner-base

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      ca-certificates=* \
      curl=7.* \
      procps=2:* \
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
      gcc=4:* \
      git=1:* \
      libc6-dev=2.* \
      libssl-dev=1.* \
      libxml2-dev=2.* \
      libxml2=2.* \
      make=4.* \
      pkg-config=0.* \
      sqlite3=3.* \
      >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

COPY Pipfile.lock /sigopt-server/Pipfile.lock
ENV PIPENV_VENV_IN_PROJECT "1"
ENV PIP_NO_BINARY lxml

RUN set -ex \
  ; pip install --upgrade --no-cache-dir "pipenv>=2023.3.20" \
  ; pipenv install --quiet --dev --ignore-pipfile \
  ; pipenv --clear \
  ; :

ENV PATH "/sigopt-server/.venv/bin:$PATH"

RUN set -ex \
  ; python -c 'import inotify, lxml, numpy, html5_parser' \
  ; :

RUN set -ex \
  ; playwright install chromium \
  ; :

RUN : \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      chromium-driver=* \
      chromium=* \
      lxde=* \
      x11vnc=* \
      xauth=* \
      xvfb=* \
      >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; ln -s /usr/bin/chromium /usr/bin/google-chrome \
  ; :

COPY src/protobuf/zigopt /sigopt-server/src/protobuf/zigopt
COPY src/python/zigopt /sigopt-server/src/python/zigopt
COPY tools/protobuf/compile.sh /compile_protobuf.sh
RUN : \
  ; /compile_protobuf.sh \
  ; :

ENV PYTHONPATH /sigopt-server/src/python:/sigopt-server/test/python:/sigopt-server/test:/sigopt-server

RUN set -ex \
  ; python -c 'import zigopt.api.prod' \
  ; :

COPY ci /sigopt-server/ci
COPY config /sigopt-server/config
COPY pytest.ini /sigopt-server/pytest.ini
COPY scripts /sigopt-server/scripts
COPY test /sigopt-server/test
COPY web /sigopt-server/web

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


FROM test-runner-base

COPY --from=test-routes /sigopt-server/artifacts/web/routes/ /sigopt-server/artifacts/web/routes/
COPY --from=test-routes /sigopt-server/artifacts/web/routes/ /routes/

COPY docker/images/test-runner/start-x11vnc.sh /start-x11vnc.sh
COPY docker/images/test-runner/entrypoint.py /entrypoint.py

ENV DISPLAY_NUM "20"
ENV DISPLAY ":$DISPLAY_NUM"
ENV GEOMETRY "1920x1080"
ENV HOME "/root"

ENTRYPOINT ["/entrypoint.py"]
