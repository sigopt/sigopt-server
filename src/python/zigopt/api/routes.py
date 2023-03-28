# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import time
from http import HTTPStatus

from flask import request

from zigopt.api.common import handler_registry
from zigopt.handlers.base.welcome import WelcomeHandler
from zigopt.net.errors import BadParamError, EndpointNotFoundError, InvalidMethodError
from zigopt.net.responses import success_response

from sigoptaux.errors import ValidationError, InvalidKeyError


HEALTH_PATH = "/health"


def log_requests(app):
  def before_request():
    if request.path != HEALTH_PATH:
      app.global_services.logging_service.with_request(request).getLogger("sigopt.requests").info(
        "%s %s",
        request.method,
        request.path,
        extra=dict(request=request),
      )

  app.before_request(before_request)

  def teardown_request(exception):
    if request.path != HEALTH_PATH:
      app.global_services.logging_service.with_request(request).getLogger("sigopt.requests").info(
        "Request time: %dms",
        (time.time() - request.start_time) * 1000,
        extra=dict(request=request),
      )

  app.teardown_request(teardown_request)


def initialize_blueprint(app):
  register_handler = handler_registry(app)
  register_handler("/", WelcomeHandler, ("GET",))

  def health_check():
    app.tracer.ignore_transaction()
    return success_response({})

  app.add_url_rule(HEALTH_PATH, view_func=health_check, methods=["HEAD", "GET", "POST"])

  # NOTE: hide OPTIONS for non-public routes because they should not be publicly visible
  @app.errorhandler(HTTPStatus.METHOD_NOT_ALLOWED)
  def invalid_method(e):
    error = EndpointNotFoundError(request.path)
    if request.path.startswith("/v1/"):
      map_adapter = app.url_map.bind(request.host, path_info=request.path)
      allowed_methods = map_adapter.allowed_methods()
      error = InvalidMethodError(allowed_methods)
    return error.get_error_response()

  @app.errorhandler(HTTPStatus.NOT_FOUND)
  def not_found(e):
    error = EndpointNotFoundError(request.path)
    return error.get_error_response()

  @app.errorhandler(ValidationError)
  def handle_validation_errors(e):
    return BadParamError(e.msg).get_error_response()

  @app.errorhandler(InvalidKeyError)
  def handle_validation_errors(e):
    return BadParamError(e.msg).get_error_response()

  app.register_error_handler(HTTPStatus.NOT_FOUND, not_found)
  app.register_error_handler(ValidationError, handle_validation_errors)
  app.register_error_handler(InvalidKeyError, handle_validation_errors)

  return app
