# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
import logging
import time

from zigopt.common import *


def time_function(logger_name, log_attributes=lambda *args, **kwargs: None):
  def decorator(f):
    def wrapped_f(f_self, *args, **kwargs):
      start = time.time()
      result = None
      try:
        result = f(f_self, *args, **kwargs)
        return result
      finally:
        end = time.time()
        logger = logging.getLogger(logger_name)
        services = getattr(f_self, "services", None)
        logger.debug(
          json.dumps(
            remove_nones(
              dict(
                className=type(f_self).__name__,
                functionName=f.__name__,
                time=(end - start),
                **(log_attributes(f_self, *args, **kwargs) or {}),
              )
            )
          ),
          extra=dict(
            request_id=services and getattr(services.request, "id", None),
            trace_id=services and getattr(services.request, "trace_id", None),
          ),
        )

    return wrapped_f

  return decorator
