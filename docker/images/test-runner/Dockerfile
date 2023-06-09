# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG NODE_MAJOR


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


FROM ubuntu:jammy-20230624 AS test-runner-base

SHELL ["/bin/bash", "-exo", "pipefail", "-c"]

ENV DEBIAN_FRONTEND noninteractive

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get upgrade -yqq >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

ENV LANG C

ARG PYTHON_MAJOR
ARG PYTHON_MINOR
RUN : \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      build-essential=* \
      ca-certificates=* \
      curl=7.* \
      git=* \
      libxslt1.1=1.1.* \
      lxde=* \
      pkg-config=* \
      python-is-python3=* \
      python3-dev="${PYTHON_MAJOR}.${PYTHON_MINOR}.*" \
      python3-minimal="${PYTHON_MAJOR}.${PYTHON_MINOR}.*" \
      python3-pip=* \
      unzip=6.* \
      x11vnc=* \
      xvfb=* \
      >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

ENV CHROMEDRIVER_VERSION "114.0.5735.90"

RUN : \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests gnupg=2.2.* >/dev/null \
  ; curl -fSs https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add \
  ; apt-get purge -yqq --autoremove gnupg2 >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list.d/google-chrome.list \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      google-chrome-stable=114.* \
      unzip=6.* \
  ; rm -rf /var/lib/apt/lists/* \
  ; curl -fSsL -o /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
  ; mkdir -p /tmp/chromedriver \
  ; unzip /tmp/chromedriver.zip -d /tmp/chromedriver \
  ; install /tmp/chromedriver/chromedriver /usr/local/bin/chromedriver \
  ; rm -r /tmp/chromedriver \
  ; :

ARG PROTOBUF_VERSION
COPY tools/protobuf/install.sh /install_protobuf.sh
RUN set -ex \
  ; /install_protobuf.sh "$PROTOBUF_VERSION" \
  ; :

WORKDIR /sigopt-server

COPY Pipfile.lock /sigopt-server/Pipfile.lock
ENV PIPENV_VENV_IN_PROJECT "1"
ENV PIP_NO_BINARY lxml

RUN set -ex \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      build-essential=12.* \
      libxml2-dev=2.9.* \
      libxslt1-dev=1.1.* \
      >/dev/null \
  ; apt-mark auto build-essential libxml2-dev libxslt1-dev \
  ; pip install --upgrade --no-cache-dir "pipenv>=2023.3.20" \
  ; pipenv install --quiet --dev --ignore-pipfile \
  ; pipenv --clear \
  ; apt-get autoremove -yqq \
  ; rm -rf /var/lib/apt/lists/* \
  ; :

ENV PATH "/sigopt-server/.venv/bin:$PATH"

RUN set -ex \
  ; python -c 'import lxml, html5_parser' \
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
