# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import logging
import pprint

from zigopt.common import *
from zigopt.services.base import Service


class RequestIdAdapter(logging.LoggerAdapter):
  def process(self, msg, kwargs):
    extra = extend_dict({}, self.extra, kwargs.pop("extra", None) or {})
    return (msg, extend_dict({"extra": extra}, kwargs))


class LoggingService(Service):
  def __init__(self, services, request=None, user=None, client=None):
    super().__init__(services)
    self.request = request
    self.user = user
    self.client = client

  def set_identity(self, user=None, client=None):
    self.user = user or self.user
    self.client = client or self.client

  def set_request(self, request):
    # This method enables us to attach a request ID and a trace ID to logging messages.
    # Call this when a request is made to replace the logging service
    # It shouldn't need to be called by developers in most cases -
    # they should just use `self.services.logging_service` and it should have a request ID
    # and a trace ID if they are available.
    self.request = request

  def reset(self):
    self.user = None
    self.client = None
    self.request = None

  @property
  def trace_id(self):
    return getattr(self.request, "trace_id", None)

  @property
  def request_id(self):
    return getattr(self.request, "id", None)

  def with_request(self, request):
    return LoggingService(self.services, request=request, user=self.user, client=self.client)

  def getLogger(self, name):
    return RequestIdAdapter(
      logging.getLogger(name),
      extra={
        "request_id": self.request_id,
        "trace_id": self.trace_id,
      },
    )

  def exception(self, name, e, exc_info, extra=None):
    msg = str(e) + ("\n" + pprint.pformat(extra) if extra else "")
    self.getLogger(name).error(msg, exc_info=exc_info, extra=extra)

  def error(self, name, msg, extra=None):
    msg = str(msg) + ("\n" + pprint.pformat(extra) if extra else "")
    self.getLogger(name).error(msg, extra=extra)

  def warning(self, name, msg, extra=None):
    msg = str(msg) + ("\n" + pprint.pformat(extra) if extra else "")
    self.getLogger(name).warning(msg, extra=extra)
