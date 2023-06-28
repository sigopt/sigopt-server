# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.handlers.validate.web_data.base import validate_web_data_update
from zigopt.handlers.web_data.base import WebDataBaseHandler
from zigopt.json.builder.web_data import WebDataJsonBuilder
from zigopt.net.errors import ForbiddenError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE


class WebDataUpdateHandler(WebDataBaseHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def parse_params(self, request):
    raw_params = request.params()
    validate_web_data_update(raw_params)

    return raw_params

  def handle(self, params):
    parent_resource_type = params["parent_resource_type"]
    web_data_type = params["web_data_type"]
    parent_resource_id = params["parent_resource_id"]
    payload = params["payload"]
    web_data_id = params["id"]

    old_web_data = self.services.web_data_service.find_by_parent_resource_id_and_id(
      parent_resource_type, web_data_type, parent_resource_id, web_data_id
    )

    # Web Data cannot change parent resoruce
    if old_web_data is None:
      raise ForbiddenError(f"{web_data_type} cannot be moved between {parent_resource_type}.")

    update_dict = {
      "updated": current_datetime(),
      "payload": payload,
    }
    query = self.services.web_data_service.find_by_parent_resource_id_and_id_query(
      parent_resource_type, web_data_type, parent_resource_id, web_data_id
    )

    self.services.database_service.update_one(query, update_dict)
    updated = self.services.web_data_service.find_by_parent_resource_id_and_id(
      parent_resource_type,
      web_data_type,
      parent_resource_id,
      web_data_id,
    )
    assert updated

    return WebDataJsonBuilder(updated)
