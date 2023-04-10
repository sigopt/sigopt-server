# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *


class ServiceBag:
  """
    A top-level container for all of our services. A service bag should be passed
    around where needed to grant access to these services. This gives us
    dependency injection, and lets us reuse services when they have a startup
    cost (such as creating DB connections).
    """

  def __init__(self, config_broker):
    self._create_services(config_broker)
    self._warmup_services()

  def _create_services(self, config_broker):
    self.config_broker = config_broker

  def _warmup_services(self):
    pass


class RequestLocalServiceBag:
  """
    A service bag that is local to a request. These should be cheap to create/destroy, and
    as such they hand off most of their work to a ServiceBag instance that is shared across
    all requests. For this reason, this bag has no warmup

    It is safe for these bags to have state that is modified throughout the request.
    """

  def __init__(self, underlying, request=None):
    self.underlying = underlying
    self.request = request

  def __getattr__(self, name):
    return getattr(self.underlying, name)

  def __dir__(self):
    return object.__dir__(self) + dir(self.underlying)
