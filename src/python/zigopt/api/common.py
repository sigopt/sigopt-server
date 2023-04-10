# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import sys
import traceback
from http import HTTPStatus

from flask import request as _request

from zigopt.common import *
from zigopt.api.request import RequestProxy, validate_api_input
from zigopt.handlers.base.handler import Handler
from zigopt.json.builder import JsonBuilder, MissingFieldError
from zigopt.net.errors import BadParamError, InvalidMethodError, RequestError, ServerError
from zigopt.net.responses import success_response

from libsigopt.aux.errors import SigoptValidationError


def handler_registry(app):
  def resolve_builder(builder, fields):
    try:
      return builder.resolve_fields(fields)
    except MissingFieldError as mfe:
      raise BadParamError(f"Could not find the field `{mfe.field_name}` in `{mfe.builder.object()}`") from mfe

  def register_handler(
    route_name, handler_cls, methods, disable_request_logging=False, provide_automatic_options=False
  ):
    handler_cls.validate_class()

    def execute_url_rule(*args, **kwargs):
      app.profiler.enable()
      app.tracer.set_transaction_name(route_name)
      services = None
      response = None
      handler = None
      exc_info = None
      config_broker = app.global_services.config_broker
      app.global_services.logging_service.set_request(_request)
      request = RequestProxy(_request)
      app.global_services.exception_logger.reset_extra()
      try:
        if not disable_request_logging:
          app.global_services.exception_logger.add_extra(
            path=request.path,
            params=request.sanitized_params(),
          )
        app.global_services.exception_logger.set_tracer(app.tracer)

        if request.method not in methods:
          raise InvalidMethodError(methods)

        args = [validate_api_input(arg) for arg in args]
        kwargs = map_dict(validate_api_input, kwargs)
        services = app.request_local_services_factory(
          app.global_services,
          request=request,
        )
        services.database_service.start_session()
        handler = handler_cls(services, request, *args, **kwargs)
        handler.prepare()

        user = handler and handler.auth and handler.auth.current_user
        client = handler and handler.auth and handler.auth.current_client
        app.global_services.logging_service.set_identity(user=user, client=client)

        app.global_services.exception_logger.add_extra(
          user_id=user.id if user else None,
          client_id=client.id if client else None,
        )

        handler_params = handler.parse_params(request)
        fields = request.optional_list_param("fields") if request.method in ["GET", "POST"] else None
        if handler_params is Handler.NO_PARAMS:
          response = handler.handle()
        else:
          response = handler.handle(handler_params)
        if request.skip_response_content:
          response = None
        elif response is None:
          response = {}
        elif isinstance(response, JsonBuilder):
          response = resolve_builder(response, fields)
        return success_response(response)
      except RequestError as e:
        exc_info = sys.exc_info()
        return e.get_error_response()
      except AssertionError:
        raise
      except SigoptValidationError:
        raise
      except Exception as e:  # pylint: disable=broad-except
        exc_info = sys.exc_info()
        user = handler and handler.auth and handler.auth.current_user
        client = handler and handler.auth and handler.auth.current_client
        app.global_services.exception_logger.log_exception(
          e,
          exc_info=exc_info,
          # If we've already generated the response and the error occurred when serializing it,
          # dump what we have so we can inspect. For this reason, we just serialize
          # the whole thing as a string instead of dumping to JSON (because serializing to JSON
          # is very likely what caused the error in the first place).
          extra={"response": napply(response, repr)},
        )
        err_msg = None
        trace = None
        if config_broker.get("errors.return_trace", default=False):
          formatted_tb = traceback.format_exception(exc_info[0], exc_info[1], exc_info[2])
          err_msg, trace = str(e), formatted_tb
        net_err = ServerError(err_msg, trace)
        return net_err.get_error_response()
      finally:
        if exc_info:
          error = exc_info[1]
          # Note: not logging request.sanitized_params() because errors are throw when request params
          # are invalid JSON
          app.global_services.logging_service.getLogger("sigopt.apiexception").exception(
            "%s %s %s",
            request.method,
            request.path,
            error,
            exc_info=exc_info,
            extra=dict(
              request=request,
              status=getattr(error, "code", HTTPStatus.INTERNAL_SERVER_ERROR.value),
            ),
          )
        if services:
          services.database_service.end_session()
        app.global_services.logging_service.reset()
        app.global_services.exception_logger.reset_extra()
        app.profiler.disable()

    execute_url_rule.__name__ = route_name
    execute_url_rule.__doc__ = handler_cls.__doc__
    # NOTE: to enable the OPTIONS method, Flask requires None for the provide_automatic_options
    # keyword. True actually disabled the OPTIONS method.
    provide_automatic_options = provide_automatic_options and None
    app.add_url_rule(
      route_name,
      f"{methods} {route_name} {handler_cls.__name__}",
      view_func=execute_url_rule,
      methods=methods,
      provide_automatic_options=provide_automatic_options,
    )

  return register_handler
