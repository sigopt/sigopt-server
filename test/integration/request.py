# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sigopt.exception import ApiException
from sigopt.ratelimit import failed_status_rate_limit
from sigopt.request_driver import RequestDriver

from zigopt.common import *


class IntegrationTestRequestor(RequestDriver):
  """
    Emits the stack trace in the ApiException message
    """

  def __init__(self, token):
    super().__init__(
      client_token=token,
    )

  def _handle_response(self, response):
    failed_status_rate_limit.clear()
    try:
      return super()._handle_response(response)
    except ApiException as e:
      err_json = e.to_json()
      trace = err_json.get("trace")
      message = e.message or ""
      if trace:
        trace_str = "\n".join(trace)
        err_json.update({"message": f"{message}\n{trace_str}"})
        raise ApiException(err_json, e.status_code) from e
      raise
