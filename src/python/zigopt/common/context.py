# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from contextlib import ExitStack
from typing import Iterable

from zigopt.common.lists import safe_iterator


class EmptyContext:
  """
    Empty context manager, does nothing. Use like

    with EmptyContext():
      pass


    Useful when you want to conditionally apply a context. For example,

    with (self.lock if use_lock else EmptyContext()):
      pass
    """

  def __enter__(self) -> None:
    pass

  def __exit__(self, *_) -> None:
    pass


class MultiContext(ExitStack):
  """
    Context manager for handling multiple context managers.
    When the input is a generator it will call __exit__ on every item that gets generated.

    Usage:

    with MultiContext(
      conn.create_any_experiment()
      for _ in range(3)
    ) as (e1, e2, e3):
      ...

    with MultiContext(
      open(filename)
      for filename in files
    ) as opened_files:
      file_list = list(opened_files)
      ...
    """

  def __init__(self, items: Iterable):
    super().__init__()
    self.item_generator = safe_iterator(items)
    self.items = None

  def __enter__(self):
    super().__enter__()
    return [self.enter_context(item) for item in self.item_generator]
