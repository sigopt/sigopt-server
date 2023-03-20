#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import argparse
import os
import signal
import sys
import threading
import time
from subprocess import Popen, TimeoutExpired

# pylint: disable=import-error
# NOTE: inotify is a Linux library that we don't want to add to requirements-dev.txt for now
from inotify.adapters import InotifyTree


# pylint: enable=import-error

NO_CHANGE_EVENTS = {
  "IN_ACCESS",
  "IN_CLOSE_NOWRITE",
  "IN_ISDIR",
  "IN_OPEN",
}


class WatcherThread(threading.Thread):
  def __init__(self, directory, file_changed_event, stop_event):
    super().__init__()
    self.directory = directory
    self.file_changed_event = file_changed_event
    self.stop_event = stop_event
    self.watcher = InotifyTree(self.directory)

  def run(self):
    for event in self.watcher.event_gen():
      if event:
        event_types = set(event[1])
        if any(event not in NO_CHANGE_EVENTS for event in event_types):
          self.file_changed_event.set()
      if self.stop_event.is_set():
        return


def get_watchers(file_changed_event, stop_event, directories):
  return [
    WatcherThread(directory=directory, file_changed_event=file_changed_event, stop_event=stop_event)
    for directory in directories
  ]


def event_loop(file_changed_event, command, initial_run):
  batch_wait_time = 0.1
  if initial_run:
    process = Popen(command, start_new_session=True)
  else:
    process = None
  while True:
    file_changed_event.wait()
    if process:
      pgrp = os.getpgid(process.pid)
      try:
        os.killpg(pgrp, signal.SIGINT)
      except ProcessLookupError:
        pass
      else:
        try:
          process.wait(timeout=10)
        except TimeoutExpired:
          try:
            os.killpg(pgrp, signal.SIGKILL)
          except ProcessLookupError:
            pass
          else:
            process.wait()
    time.sleep(batch_wait_time)
    file_changed_event.clear()
    process = Popen(command, start_new_session=True)


def main(args):
  file_changed_event = threading.Event()
  stop_event = threading.Event()
  watcher_threads = get_watchers(file_changed_event, stop_event, args.dir)
  for thread in watcher_threads:
    thread.start()
  try:
    event_loop(file_changed_event, args.command, args.initial_run)
  finally:
    stop_event.set()
    for thread in watcher_threads:
      thread.join()
  return 0


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--dir", action="append", required=True)
  parser.add_argument("--initial-run", action="store_true")
  parser.add_argument("command", nargs=argparse.REMAINDER)
  args = parser.parse_args()
  sys.exit(main(args))
