# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.validate.web_data.base import validate_web_data_delete
from zigopt.handlers.web_data.base import WebDataBaseHandler
from zigopt.net.errors import NotFoundError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE


class WebDataDeleteHandler(WebDataBaseHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def parse_params(self, request):
    raw_params = request.params()
    validate_web_data_delete(raw_params)

    return raw_params

  def handle(self, params):  # type: ignore
    parent_resource = params["parent_resource_type"]
    web_data_type = params["web_data_type"]
    parent_resource_id = params["parent_resource_id"]
    web_data_id = params["id"]

    # Ensure the id is for the right resource
    web_data = self.services.web_data_service.find_by_parent_resource_id_and_id(
      parent_resource, web_data_type, parent_resource_id, web_data_id
    )
    if web_data is None:
      raise NotFoundError(
        f"Cannot find web data of type: {web_data_type}, with parent resource: {parent_resource} and id: {web_data_id}."
      )

    self.services.web_data_service.delete(web_data_id)

    return {}
