# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
ARG BUILD_TAG=build


FROM sigopt-images/zigopt:${BUILD_TAG}

COPY config /sigopt-server/config

RUN set -ex \
  ; useradd produser \
  ; :

USER produser

ENTRYPOINT ["python", "-m", "zigopt.queue.api"]
