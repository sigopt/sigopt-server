# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import logging
import pprint
from collections.abc import Mapping, MutableMapping
from typing import Any

from zigopt.common import *
from zigopt.api.request import RequestProxy
from zigopt.client.model import Client
from zigopt.services.base import Service
from zigopt.user.model import User


class RequestIdAdapter(logging.LoggerAdapter):
  extra: dict[str, object]

  def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, MutableMapping[str, Any]]:
    extra = extend_dict({}, self.extra, kwargs.pop("extra", None) or {})
    return (msg, extend_dict({"extra": extra}, kwargs))


class LoggingService(Service):
  request: RequestProxy | None
  user: User | None
  client: Client | None

  def __init__(
    self, services, request: RequestProxy | None = None, user: User | None = None, client: Client | None = None
  ):
    super().__init__(services)
    self.request = request
    self.user = user
    self.client = client

  def set_identity(self, user: User | None = None, client: Client | None = None) -> None:
    self.user = user or self.user
    self.client = client or self.client

  def set_request(self, request: RequestProxy) -> None:
    # This method enables us to attach a request ID and a trace ID to logging messages.
    # Call this when a request is made to replace the logging service
    # It shouldn't need to be called by developers in most cases -
    # they should just use `self.services.logging_service` and it should have a request ID
    # and a trace ID if they are available.
    self.request = request

  def reset(self) -> None:
    self.user = None
    self.client = None
    self.request = None

  @property
  def trace_id(self) -> str | None:
    if self.request is None:
      return None
    return getattr(self.request, "trace_id", None)

  @property
  def request_id(self) -> str | None:
    if self.request is None:
      return None
    return getattr(self.request, "id", None)

  def with_request(self, request: RequestProxy) -> "LoggingService":
    return LoggingService(self.services, request=request, user=self.user, client=self.client)

  def getLogger(self, name: str) -> RequestIdAdapter:
    return RequestIdAdapter(
      logging.getLogger(name),
      extra={
        "request_id": self.request_id,
        "trace_id": self.trace_id,
      },
    )

  def exception(self, name: str, e: BaseException, exc_info: Any, extra: Mapping | None = None) -> None:
    msg = str(e) + ("\n" + pprint.pformat(extra) if extra else "")
    self.getLogger(name).error(msg, exc_info=exc_info, extra=extra)

  def error(self, name: str, msg: str, extra: Mapping | None = None) -> None:
    msg = str(msg) + ("\n" + pprint.pformat(extra) if extra else "")
    self.getLogger(name).error(msg, extra=extra)

  def warning(self, name: str, msg: str, extra: Mapping | None = None) -> None:
    msg = str(msg) + ("\n" + pprint.pformat(extra) if extra else "")
    self.getLogger(name).warning(msg, extra=extra)
