# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
import time
import uuid

from flask import Request as RequestBase

from zigopt.common import *
from zigopt.api.paging import deserialize_paging_marker
from zigopt.handlers.validate.validate_dict import ValidationType, validate_type
from zigopt.net.errors import BadParamError, RequestError
from zigopt.pagination.paging import PagingRequest, SortRequest

from libsigopt.aux.errors import MissingParamError


DEFAULT_PAGING_MAX_LIMIT = 1000


def validate_api_input_string(string):
  assert isinstance(string, str)
  # Postgres treats any string with a NUL-byte (the Unicode code point 0, represented as '\0' in UTF-8)
  # as invalid, even though it is valid UTF-8 string.
  # We are natively rejecting all other invalid UTF-8 so we just need to reject strings with NUL bytes
  # as a special case.
  if "\0" in string:
    raise BadParamError(f"Invalid string parameter: {string}")
  return string


def validate_api_input(val):
  if is_string(val):
    return validate_api_input_string(val)
  return val


def object_pairs_hook_raise_on_duplicates(ordered_pairs):
  """Reject duplicate keys.

    Intended to be used as the value of ``object_pairs_hook`` in
    ``json.load`` or ``json.loads``.
    See: https://docs.python.org/2/library/json.html#json.load

    :param ordered_pairs: *ordered* list of (key, value) pairs from json decode
    :type ordered_pairs: list
    :return: validated dict with unique (key, value) pairs
    :rtype: dict

    """
  output_dict = {}
  for key, value in ordered_pairs:
    key = validate_api_input(key)
    value = validate_api_input(value)
    if key in output_dict:
      raise BadParamError(f"Duplicate key value in JSON document: {key}")
    else:
      output_dict[key] = value
  return output_dict


class InvalidJsonValue(BadParamError):
  pass


def parse_constant(constant):
  """Reject invalid JSON values"""
  assert constant in ("-Infinity", "Infinity", "NaN")
  raise InvalidJsonValue(constant)


def parse_float(float_str):
  ret = float(float_str)
  if not is_number(ret):
    raise InvalidJsonValue(float_str)
  return ret


def as_json(string, encoding="utf-8"):
  """Deserialize a str holding a JSON document into a Python dict.

    :param string: serialized json data
    :type string: str
    :return: deserialized json string
    :rtype: dict

    """
  object_pairs_hook = object_pairs_hook_raise_on_duplicates

  try:
    return json.loads(
      string.decode(encoding),
      object_pairs_hook=object_pairs_hook,
      parse_constant=parse_constant,
      parse_float=parse_float,
    )
  except json.JSONDecodeError as e:
    raise BadParamError("Invalid json: " + string.decode(encoding)) from e
  except ValueError as e:
    raise BadParamError(f"Error parsing json: {e}") from e


class RequestProxy(object):
  """
    Exposes a limited subset of Flask request endpoints, so that
    Handler implementations do not depend directly on Flask.
    This should also make it easier to mock endpoints for testing
    """

  def __init__(self, request):
    self.request = request

  @property
  def id(self):
    return self.request.id

  @property
  def trace_id(self):
    return self.request.trace_id

  @property
  def path(self):
    return self.request.path

  @property
  def method(self):
    return self.request.method

  @property
  def user_agent(self):
    return self.request.user_agent

  @property
  def headers(self):
    return self.request.headers

  @property
  def skip_response_content(self):
    return self.request.skip_response_content

  def params(self):
    return self.request.params()

  def optional_param(self, *args, **kwargs):
    return self.request.optional_param(*args, **kwargs)

  def required_param(self, *args, **kwargs):
    return self.request.required_param(*args, **kwargs)

  def optional_int_param(self, *args, **kwargs):
    return self.request.optional_int_param(*args, **kwargs)

  def optional_bool_param(self, *args, **kwargs):
    return self.request.optional_bool_param(*args, **kwargs)

  def optional_list_param(self, *args, **kwargs):
    return self.request.optional_list_param(*args, **kwargs)

  def get_sort(self, *args, **kwargs):
    return self.request.get_sort(*args, **kwargs)

  def get_paging(self, *args, **kwargs):
    return self.request.get_paging(*args, **kwargs)

  def optional_api_token(self, *args, **kwargs):
    return self.request.optional_api_token(*args, **kwargs)

  def optional_client_token(self, *args, **kwargs):
    return self.request.optional_client_token(*args, **kwargs)

  def optional_user_token(self, *args, **kwargs):
    return self.request.optional_user_token(*args, **kwargs)

  def sanitized_params(self, *args, **kwargs):
    return self.request.sanitized_params(*args, **kwargs)

  def sanitized_headers(self, *args, **kwargs):
    return self.request.sanitized_headers(*args, **kwargs)


class Request(RequestBase):
  _MISSING = object()

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.id = self.headers.get("X-Request-Id", f"python-{uuid.uuid1()}")
    self.trace_id = self.headers.get("X-Trace-Id", self.id)
    self.start_time = time.time()
    self._params = self._MISSING

  @property
  def want_form_data_parsed(self):
    return False

  @property
  def skip_response_content(self):
    return self.headers.get("X-Response-Content") == "skip"

  # scrubs out sensitive parameters
  sensitive_params = set(
    (
      "user_token",
      "client_token",
      "old_password",
      "new_password",
      "password",
      "password_reset_code",
      "invite_code",
      "code",
      "stripe_token",
    )
  )

  # Don't count empty json as malformed json
  def on_json_loading_failed(self, e):
    if self.data == b"":
      return {}
    if isinstance(e, RequestError):
      raise e
    raise BadParamError("Malformed json in request body") from e

  def params(self):
    ret = self._params
    if ret is self._MISSING:
      if self.method in ("GET", "DELETE"):
        self._params = {validate_api_input(k): validate_api_input(v) for k, v in self.args.items()}
      elif self.method in ("PUT", "POST", "MERGE"):
        json_blob = self.parse_json()
        self._params = coalesce(json_blob, {})
    return self._params

  # Use instead of flask.wrappers.Request.get_json so we can use custom json deserialization
  def parse_json(self):
    # x-www-form-urlencoded is the default content type, so if users are calling
    # the API from CURL without a Content-Type header we should assume JSON
    # if the user manually provided a Content-Type then we won't try to parse
    # the body as JSON
    if self.mimetype not in (None, "", "application/x-www-form-urlencoded", "application/json"):
      return None

    text = self.data
    encoding = self.mimetype_params.get("charset") or "utf-8"
    try:
      ret = as_json(
        text,
        encoding=encoding,
      )
    except BadParamError as e:
      return self.on_json_loading_failed(e)
    if not isinstance(ret, dict):
      raise BadParamError("Request body must be a JSON object")
    return ret

  def optional_param(self, name):
    """Retrieve ``name`` from flask HTTP request."""
    unvalidated = self.params().get(name)
    return napply(unvalidated, lambda v: validate_type(v, ValidationType.string, key=name))

  def required_param(self, name):
    """Retrieve ``name`` from flask HTTP request and *fail* if ``name`` is not found."""
    value = self.optional_param(name)
    if value is not None:
      return value
    else:
      raise MissingParamError(name)

  def optional_int_param(self, name):
    assert self.method in ("GET", "DELETE"), "Must use get_with_validation for non-query arguments"
    unvalidated = self.params().get(name)
    return napply(unvalidated, lambda v: validate_type(v, ValidationType.integer_string, key=name))

  def optional_bool_param(self, name):
    assert self.method in ("GET", "DELETE"), "Must use get_with_validation for non-query arguments"
    unvalidated = napply(self.params().get(name), self.string_to_bool)
    return napply(unvalidated, lambda v: validate_type(v, ValidationType.boolean, key=name))

  def optional_list_param(self, name):
    """
        Fetches optional list param as comma separated values from url-encoded param requests, otherwise as json arrays.
        In the url-encoded params case, ?id= is distinguished from ?id=1,2,3 and further from the empty query string.
        Calls to request.optional_list_param('id') will yield [], [1,2,3] and None, respectively.

        """
    assert self.method in ("GET", "POST", "DELETE"), "Must use get_with_validation for non-query arguments"
    param_string = self.params().get(name)
    param_value = param_string.split(",") if param_string else None
    if param_value is None:
      return None
    if not isinstance(param_value, list):
      raise BadParamError("Invalid list value: " + param_value)
    return param_value

  def get_sort(self, default_field, default_ascending=False):
    field = self.optional_param("sort") or default_field
    ascending = coalesce(self.optional_bool_param("ascending"), default_ascending)
    return SortRequest(field, ascending)

  def _parse_marker(self, name):
    serialized_marker = self.optional_param(name)
    if serialized_marker is None:
      return None
    return deserialize_paging_marker(serialized_marker)

  def get_paging(self, max_limit=DEFAULT_PAGING_MAX_LIMIT):
    limit = self.optional_int_param("limit")
    if limit is None:
      limit = max_limit
    if limit < 0:
      raise BadParamError(f"Invalid limit: {limit}")
    if max_limit is not None and limit > max_limit:
      raise BadParamError(f"Exceeded maximum limit: {max_limit}")

    before = self._parse_marker("before")
    after = self._parse_marker("after")

    return PagingRequest(
      limit=limit,
      before=before,
      after=after,
    )

  def string_to_bool(self, value):
    if value == "1" or value.lower() == "true":
      return True
    elif value == "0" or value.lower() == "false":
      return False
    raise BadParamError("Invalid boolean value: " + value)

  def sanitized_params(self):
    def _sanitized_params(params):
      if is_sequence(params):
        return [_sanitized_params(p) for p in params]
      elif is_mapping(params):
        return dict(
          (
            (key, _sanitized_params(value) if key not in self.sensitive_params else "*****")
            for (key, value) in params.items()
          )
        )
      else:
        return params

    return _sanitized_params(self.params())

  def sanitized_headers(self):
    sensitive_headers = [
      "Authorization",
      "X-SigOpt-Client-Token",
      "X-SigOpt-User-Token",
      "X-Nginx-Secret",
    ]

    def sanitize_value(k, v):
      if k in sensitive_headers:
        if v is None or v == "":
          return "*"
        else:
          return "*****"
      else:
        return v

    return dict((k, sanitize_value(k, v)) for (k, v) in self.headers.items())

  def _auth_username(self):
    auth = self.authorization
    return auth.username if auth else None

  def optional_api_token(self):
    return self._auth_username()

  def optional_client_token(self):
    return self._auth_username()

  def optional_user_token(self):
    return self._auth_username()
