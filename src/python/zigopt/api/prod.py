# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from flask import Flask

from zigopt.api.errors import InvalidKeyError, ValidationError
from zigopt.api.request import Request
from zigopt.api.routes import initialize_blueprint as initialize_base_blueprint
from zigopt.api.routes import log_requests
from zigopt.api.v1.routes import initialize_blueprint as initialize_v1_blueprint
from zigopt.net.errors import BadParamError
from zigopt.net.responses import success_response
from zigopt.services.api import ApiRequestLocalServiceBag, ApiServiceBag


class ProdApp(Flask):
  ServiceBag = ApiServiceBag
  RequestLocalServiceBag = ApiRequestLocalServiceBag

  def __init__(self, profiler, tracer, config_broker):
    super().__init__(__name__)
    self.request_class = Request
    self.profiler = profiler
    self.tracer = tracer
    self.config_broker = config_broker

    config_broker.log_configs()

    def handle_validation_errors(e):
      return BadParamError(e.msg).get_error_response()

    self.global_services = self.ServiceBag(config_broker, is_qworker=False)
    self.request_local_services_factory = self.RequestLocalServiceBag

    log_requests(self)

    self.register_error_handler(ValidationError, handle_validation_errors)
    self.register_error_handler(InvalidKeyError, handle_validation_errors)

    initialize_base_blueprint(self)
    self.register_blueprint(initialize_v1_blueprint(self), url_prefix="/v1")

    self.register_error_handler(ValidationError, handle_validation_errors)
    self.register_error_handler(InvalidKeyError, handle_validation_errors)

  def make_default_options_response(self):
    return success_response({})
