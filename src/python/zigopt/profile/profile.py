# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import time


class Profiler(object):
  def __init__(self):
    import cProfile
    import tracemalloc

    tracemalloc.start()
    self.profile = cProfile.Profile()
    self.initial_tracemalloc_snapshot = tracemalloc.take_snapshot()
    self.last_tracemalloc_snapshot = self.initial_tracemalloc_snapshot
    self.start_time = None
    self.total_time = 0.0

  def enable(self):
    self.start_time = time.time()
    self.profile.enable()

  def disable(self):
    import tracemalloc

    self.profile.disable()
    self.last_tracemalloc_snapshot = tracemalloc.take_snapshot()
    self.total_time += time.time() - self.start_time
    self.start_time = None

  def print_stats(self, *args, **kwargs):
    try:
      self.profile.print_stats(*args, **kwargs)
      print(f"TOTAL TIME: {self.total_time}")  # noqa: T001
    except TypeError:
      # NOTE: TypeError occurs when the profiler has not collected any stats
      pass
    top_stats = self.last_tracemalloc_snapshot.compare_to(self.initial_tracemalloc_snapshot, "lineno")
    for stat in top_stats[:25]:
      print(stat)  # noqa: T001

  def dump_stats(self, filename, *args, **kwargs):
    try:
      self.profile.dump_stats(filename)
    except TypeError:
      pass


class NullProfiler(object):
  def enable(self):
    pass

  def disable(self):
    pass

  def print_stats(self, *args, **kwargs):
    pass
