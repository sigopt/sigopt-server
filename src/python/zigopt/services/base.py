# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import warnings


class Service(object):
  """
    Base class for all services.
    """

  def __init__(self, services):
    self.services = services

  @property
  def logger(self):
    logger_name = getattr(self, "logger_name", None)
    if not logger_name:
      warnings.warn("Using Service.logger without a specified logger_name, falling back to root logger")
      logger_name = "sigopt"
    return self.services.logging_service.getLogger(logger_name)
