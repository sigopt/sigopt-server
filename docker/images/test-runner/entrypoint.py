#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# pylint: disable=W1509

import os
import signal
import subprocess
import sys
from security import safe_command


DISPLAY_NUM = os.environ["DISPLAY_NUM"]
GEOMETRY = os.environ["GEOMETRY"]

with open("/dev/null", "w", encoding="utf-8") as devnull:
  with subprocess.Popen(
    [
      "xvfb-run",
      f"--server-num={DISPLAY_NUM}",
      "--listen-tcp",
      f"--server-args=-screen 0 {GEOMETRY}x24 -fbdir /var/tmp -listen tcp -noreset -ac +extension RANDR",
      "--error-file=/dev/stderr",
      "startlxde",
    ],
    stdout=devnull,
    preexec_fn=os.setpgrp,
  ) as xvfb:
    with subprocess.Popen(["/start-x11vnc.sh"], stdout=devnull, stderr=devnull, preexec_fn=os.setpgrp) as x11vnc:
      with safe_command.run(subprocess.Popen, sys.argv[1:]) as main:
        signal.signal(signal.SIGINT, lambda *_: main.send_signal(signal.SIGINT))
        return_code = main.wait()

      for proc in (xvfb, x11vnc):
        proc.kill()

  sys.exit(return_code)
