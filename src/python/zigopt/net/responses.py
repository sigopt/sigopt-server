# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
from enum import Enum
from http import HTTPStatus

from flask import request

from zigopt.common import *
from zigopt.net.headers import RESPONSE_HEADERS


def get_response_headers(req):
  # TODO(SN-997): what about cors_app_response_headers? Need app_url here...
  return RESPONSE_HEADERS.copy()


class TokenStatus(Enum):
  REVOKED = 1
  EXPIRED = 2
  INVALID_PERMISSIONS = 3
  NEEDS_EMAIL_VERIFICATION = 4


def success_response(body):
  headers = get_response_headers(request)
  if body is None:
    return ("", HTTPStatus.NO_CONTENT.value, headers)
  else:
    return (dump_json(body), HTTPStatus.OK.value, headers)


# Prevent JSON from being incorrectly interpreted as HTML. This is not strictly necessary but
#  a) It may prevent old misbehaving browsers from ignoring the Content-Type and doing the wrong thing
#  b) It came up in a customer security review, so make them happy
class OurJsonEncoder(json.JSONEncoder):
  def encode(self, o):
    encoded = super().encode(o)
    return encoded.replace("&", "\\u0026").replace("<", "\\u003C").replace(">", "\\u003E")


def dump_json(json_input):
  # Format the response so that users who are using curl have a nicer experience
  return (
    json.dumps(
      json_input,
      cls=OurJsonEncoder,
      allow_nan=False,
      indent=2,
    )
    + "\n"
  )
