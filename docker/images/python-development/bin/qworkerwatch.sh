#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

: "${MESSAGE_GROUP:?Missing MESSAGE_GROUP environment variable}"

if [ -n "$_RUN" ]; then
  echo "starting qworker"
  while true; do
    # NOTE: The only time that this command should exit gracefully
    # is if the running process receives a SIGINT. Other instances like
    # uncaught exceptions and reaching the message limit should cause the worker to restart.
    # The loop could probably break for a SyntaxError, but that's not straightforward to catch here.
    if python -m zigopt.queue.api "$MESSAGE_GROUP" --graceful-exit-code=1; then
      break
    fi
    sleep 1
  done
else
  _RUN=x run_command_on_change.py --dir=/sigopt-server/libsigopt --dir=/sigopt-server/src/python/zigopt --initial-run "$0"
fi
