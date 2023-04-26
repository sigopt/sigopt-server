# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.validate.web_data.base import validate_web_data_create
from zigopt.handlers.web_data.base import WebDataBaseHandler
from zigopt.json.builder.web_data import WebDataJsonBuilder
from zigopt.net.errors import ForbiddenError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE
from zigopt.web_data.model import WebData


class WebDataCreateHandler(WebDataBaseHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def parse_params(self, request):
    raw_params = request.params()
    validate_web_data_create(raw_params)

    return raw_params

  def handle(self, params):
    parent_resource_type = params["parent_resource_type"]
    web_data_type = params["web_data_type"]
    parent_resource_id = params["parent_resource_id"]
    payload = params["payload"]
    display_name = params["display_name"]

    web_data_limit = self.web_data_limits[parent_resource_type][web_data_type]

    current_count = self.services.web_data_service.count(parent_resource_type, web_data_type, parent_resource_id)
    if current_count >= web_data_limit:
      raise ForbiddenError(f"There is a limit of {web_data_limit} for the web data type: {web_data_type}")

    new_web_data = WebData(
      parent_resource_type=parent_resource_type,
      web_data_type=web_data_type,
      parent_resource_id=parent_resource_id,
      display_name=display_name,
      payload=payload,
      created_by=(self.auth and self.auth.current_user and self.auth.current_user.id),
    )

    self.services.database_service.insert(new_web_data)

    return WebDataJsonBuilder(new_web_data)
