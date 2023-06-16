# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import logging
import warnings
from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:
  from zigopt.log.service import LoggingService
  from zigopt.services.api import ApiRequestLocalServiceBag, ApiServiceBag


class HasLoggingService(Protocol):
  logging_service: "LoggingService"


class BaseService:
  """
    Base class for all services.
    """

  services: HasLoggingService

  @property
  def logger(self) -> logging.LoggerAdapter | logging.Logger:
    logger_name = getattr(self, "logger_name", None)
    if not logger_name:
      warnings.warn("Using Service.logger without a specified logger_name, falling back to root logger")
      logger_name = "sigopt"
    return self.services.logging_service.getLogger(logger_name)


class GlobalService(BaseService):
  """
    Base class for services that will be available in the global service bag.
    """

  services: "ApiServiceBag"

  def __init__(self, services: "ApiServiceBag"):
    self.services = services


class Service(BaseService):
  """
    Base class for services available in the request local service bag.
    """

  services: "ApiRequestLocalServiceBag"

  def __init__(self, services: "ApiRequestLocalServiceBag"):
    self.services = services
