# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Exception classes for ``sigopt-server``.

Several of these alias HTTP status codes:
http://en.wikipedia.org/wiki/List_of_HTTP_status_codes

"""
import json
from http import HTTPStatus

from flask import request

from zigopt.brand.constant import PRODUCT_NAME
from zigopt.net.responses import TokenStatus, dump_json, get_response_headers


class RequestError(Exception):
  """Base exception class for HTTP request errors."""

  def __init__(self, message, code, token_status=None):
    super().__init__(message)
    assert isinstance(code, HTTPStatus)
    assert 300 <= code.value < 600, f"HTTP Code must indicate an error: {code}"
    self.code = code.value
    self.token_status = token_status

  def update_response_headers(self, headers):
    pass

  def get_response_body(self):
    response_body = {
      "message": str(self),
      "status": self.code,
    }
    if self.token_status:
      response_body["token_status"] = {
        TokenStatus.REVOKED: "revoked",
        TokenStatus.EXPIRED: "expired",
        TokenStatus.INVALID_PERMISSIONS: "invalid_permissions",
        TokenStatus.NEEDS_EMAIL_VERIFICATION: "needs_email_verification",
      }[self.token_status]
    return response_body

  def get_error_response(self):
    headers = get_response_headers(request)
    self.update_response_headers(headers)
    response_body = self.get_response_body()
    return (
      dump_json(response_body),
      self.code,
      headers,
    )


class UnprocessableEntityError(RequestError):
  def __init__(self, msg):
    super().__init__(msg, HTTPStatus.UNPROCESSABLE_ENTITY)


class BadParamError(RequestError):
  def __init__(self, msg):
    super().__init__(msg, HTTPStatus.BAD_REQUEST)


class ConflictingDataError(RequestError):
  def __init__(self, msg):
    super().__init__(msg, HTTPStatus.CONFLICT)


class MissingParamError(BadParamError):
  def __init__(self, param, msg=None):
    if not msg:
      msg = f"Missing required param: {param}"

    super().__init__(msg)


class MissingJsonKeyError(BadParamError):
  def __init__(self, param, json_obj):
    msg = f'Missing required json key "{param}" in: {json.dumps(json_obj)}'

    super().__init__(msg)
    self.missing_json_key = param


# Note: TypeError is a stdlib name
class InvalidTypeError(BadParamError):
  def __init__(self, value, expected_type, key=None):
    try:
      value_str = json.dumps(value)
      value_sep = f": {value_str} - "
    except TypeError:
      value_sep = ", "
    if key:
      msg = f"Invalid type for {key}{value_sep}expected type {str(expected_type)}"
    else:
      msg = f"Invalid type{value_sep}expected type {str(expected_type)}"

    super().__init__(msg)
    self.value = value
    self.expected_type = expected_type


# Note: ValueError is a stdlib name
class InvalidValueError(BadParamError):
  def __init__(self, msg):
    super().__init__(msg)


# Note: KeyError is a stdlib name
class InvalidKeyError(BadParamError):
  def __init__(self, key, msg=None):
    if not msg:
      msg = f"Invalid key: {key}"
    super().__init__(msg)
    self.invalid_key = key


class ServerError(RequestError):
  def __init__(self, msg=None, trace=None):
    if not msg:
      msg = "An unexpected server error has occurred."
    super().__init__(msg, HTTPStatus.INTERNAL_SERVER_ERROR)
    self.trace = trace

  def get_response_body(self):
    response_body = super().get_response_body()
    if self.trace:
      response_body["trace"] = self.trace
    return response_body


class ForbiddenError(RequestError):
  def __init__(self, msg=None, token_status=None, expired=False):
    if not msg:
      msg = "You are not authorized to access this resource."
    super().__init__(msg, HTTPStatus.FORBIDDEN, token_status=token_status)


class UnauthorizedError(RequestError):
  UNAUTHORIZED_RESPONSE_HEADER = {"WWW-Authenticate": f'Basic realm="{PRODUCT_NAME} API"'}

  def __init__(self, msg=None, www_authenticate=False):
    if not msg:
      msg = "Please provide authentication to access this resource."
    super().__init__(msg, HTTPStatus.UNAUTHORIZED)
    self.www_authenticate = www_authenticate

  def update_response_headers(self, headers):
    if self.www_authenticate:
      headers.update(self.UNAUTHORIZED_RESPONSE_HEADER)


class NotFoundError(RequestError):
  def __init__(self, msg=None, token_status=None):
    if not msg:
      msg = "The requested resource could not be found"
    super().__init__(msg, HTTPStatus.NOT_FOUND, token_status=token_status)


class EndpointNotFoundError(NotFoundError):
  def __init__(self, path, msg=None):
    parts = [p for p in path.lstrip("/").split("/") if p]
    if parts:
      if parts[0] == "v1":
        msg = f"Endpoint not found: {path}"
      else:
        msg = f"Endpoint not found: {path}. (Endpoint paths must begin with /v1)"
    super().__init__(msg)


class InvalidMethodError(RequestError):
  def __init__(self, methods):
    super().__init__(
      f"This endpoint accepts only the following methods: {methods}",
      HTTPStatus.METHOD_NOT_ALLOWED,
    )


class TooManyRequestsError(RequestError):
  def __init__(self, msg=None):
    if not msg:
      msg = "This client has issued too many requests"
    super().__init__(msg, HTTPStatus.TOO_MANY_REQUESTS)


class RedirectException(RequestError):
  def __init__(self, location, msg="The requested resource has moved", code=HTTPStatus.MOVED_PERMANENTLY):
    assert 300 <= code.value < 400
    super().__init__(msg, code)
    self.location = location

  def update_response_headers(self, headers):
    headers["Location"] = self.location

  def get_response_body(self):
    response_body = super().get_response_body()
    response_body.update(
      {
        "location": self.location,
      }
    )
    return response_body
