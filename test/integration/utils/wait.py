# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import logging

import backoff


logger = logging.getLogger("test_waiter")
logger.setLevel(logging.ERROR)


def wait_for(func, timeout_message="Timed out", timeout=10):
  def wrap_func():
    try:
      result = func()
    except AssertionError as ae:
      if type(ae) is not AssertionError:  # pylint: disable=unidiomatic-typecheck
        raise
      raise TimeoutError(timeout_message) from ae
    if not result:
      raise TimeoutError(timeout_message)
    return result

  backoff_func = backoff.on_exception(backoff.expo, TimeoutError, max_time=timeout, logger=logger)(wrap_func)
  return backoff_func()
