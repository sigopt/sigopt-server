# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG BUILD_TAG=build


FROM sigopt/node:${BUILD_TAG} AS test-routes

COPY web /sigopt-server/web
COPY config/circleci.json /sigopt-server/config/circleci.json
COPY config/development.json /sigopt-server/config/development.json
COPY scripts/compile/generate_routes /sigopt-server/scripts/compile/generate_routes
COPY .babelrc /sigopt-server/.babelrc
COPY webpack.config.script.babel.js /sigopt-server/webpack.config.script.babel.js

RUN ./scripts/compile/generate_routes config/circleci.json


FROM sigopt/test-runner:${BUILD_TAG}

SHELL ["/bin/bash", "-exo", "pipefail", "-c"]

ENV CHROMEDRIVER_VERSION "111.0.5563.41"

RUN : \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests gnupg=2.2.* >/dev/null \
  ; curl -fSs https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add \
  ; apt-get purge -yqq --autoremove gnupg2 >/dev/null \
  ; rm -rf /var/lib/apt/lists/* \
  ; echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list.d/google-chrome.list \
  ; apt-get update -yqq >/dev/null \
  ; apt-get install -yqq --no-install-recommends --no-install-suggests \
      google-chrome-stable=111.* \
      unzip=6.* \
  ; rm -rf /var/lib/apt/lists/* \
  ; curl -fSsL -o /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
  ; mkdir -p /tmp/chromedriver \
  ; unzip /tmp/chromedriver.zip -d /tmp/chromedriver \
  ; install /tmp/chromedriver/chromedriver /usr/local/bin/chromedriver \
  ; rm -r /tmp/chromedriver \
  ; :

COPY --from=test-routes /sigopt-server/artifacts/web/routes/ /sigopt-server/artifacts/web/routes/

COPY docker/images/test-runner-web/start-x11vnc.sh /start-x11vnc.sh
COPY docker/images/test-runner-web/entrypoint.py /entrypoint.py

ENV DISPLAY_NUM "20"
ENV DISPLAY ":$DISPLAY_NUM"
ENV GEOMETRY "1920x1080"
ENV HOME "/root"

ENTRYPOINT ["/entrypoint.py"]
