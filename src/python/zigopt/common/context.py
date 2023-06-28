# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0


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
