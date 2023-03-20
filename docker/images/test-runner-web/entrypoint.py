#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# pylint: disable=W1509

import os
import signal
import subprocess
import sys


DISPLAY_NUM = os.environ["DISPLAY_NUM"]
GEOMETRY = os.environ["GEOMETRY"]

with open("/dev/null", "w") as devnull:
  xvfb = subprocess.Popen(
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
  )

  x11vnc = subprocess.Popen(["/start-x11vnc.sh"], stdout=devnull, stderr=devnull, preexec_fn=os.setpgrp)

  main = subprocess.Popen(sys.argv[1:])
  signal.signal(signal.SIGINT, lambda *_: main.send_signal(signal.SIGINT))
  return_code = main.wait()

  for proc in (xvfb, x11vnc):
    proc.kill()
  for proc in (xvfb, x11vnc):
    proc.wait()

  sys.exit(return_code)
