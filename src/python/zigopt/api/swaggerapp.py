# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from flask import Flask

from zigopt.api.request import Request
from zigopt.api.routes import initialize_blueprint as initialize_base_blueprint
from zigopt.api.routes import log_requests
from zigopt.api.v1.routes import initialize_blueprint as initialize_v1_blueprint
from zigopt.exception.logger import ExceptionLogger
from zigopt.log.service import LoggingService
from zigopt.net.responses import success_response
from zigopt.profile.profile import NullProfiler
from zigopt.profile.tracer import NullTracer
from zigopt.services.bag import ServiceBag
from zigopt.services.disabled import DisabledService


class DummyServiceBag(ServiceBag):
  def __init__(self, config_broker):
    super().__init__(config_broker)
    super()._create_services(config_broker)
    self.database_connection_service = DisabledService(self)
    self.exception_logger = ExceptionLogger(self)
    self.immediate_email_sender = DisabledService(self)
    self.logging_service = LoggingService(self)
    self.smtp_email_service = DisabledService(self)


class SwaggerApp(Flask):
  ServiceBag = DummyServiceBag
  RequestLocalServiceBag = DummyServiceBag

  def __init__(self, config_broker):
    super().__init__(__name__)
    self.request_class = Request
    self.config_broker = config_broker
    self.profiler = NullProfiler()
    self.tracer = NullTracer()

    config_broker.log_configs()

    self.global_services = self.ServiceBag(config_broker=config_broker)
    self.request_local_services_factory = self.RequestLocalServiceBag

    log_requests(self)
    initialize_base_blueprint(self)
    self.register_blueprint(initialize_v1_blueprint(self), url_prefix="/v1")

  def make_default_options_response(self):
    return success_response({})
