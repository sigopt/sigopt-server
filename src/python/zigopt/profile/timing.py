# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
import logging
import time
from functools import wraps
from typing import Any, Callable, Mapping, ParamSpec, TypeVar

from zigopt.common import *


TParams = ParamSpec("TParams")
TResult = TypeVar("TResult")
TWrapped = Callable[TParams, TResult]


def time_function(
  logger_name: str, log_attributes: Callable[TParams, Mapping[str, Any] | None] = lambda *args, **kwargs: {}
) -> Callable[[TWrapped], TWrapped]:
  def decorator(f: TWrapped) -> TWrapped:
    @wraps(f)
    def wrapped_f(*args, **kwargs):
      f_self = args[0]
      start = time.time()
      result = None
      try:
        result = f(*args, **kwargs)
        return result
      finally:
        end = time.time()
        logger = logging.getLogger(logger_name)
        services = getattr(f_self, "services", None)
        logger.debug(
          json.dumps(
            remove_nones_mapping(
              dict(
                className=type(f_self).__name__,
                functionName=f.__name__,
                time=(end - start),
                **(log_attributes(*args, **kwargs) or {}),
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
