# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.validate.web_data.base import validate_web_data_list
from zigopt.handlers.web_data.base import WebDataBaseHandler
from zigopt.json.builder import PaginationJsonBuilder
from zigopt.json.builder.web_data import WebDataJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class WebDataListHandler(WebDataBaseHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def parse_params(self, request):
    raw_params = request.params()
    validate_web_data_list(raw_params)

    return raw_params

  def handle(self, params):
    parent_resource_type = params["parent_resource_type"]
    web_data_type = params["web_data_type"]
    parent_resource_id = params["parent_resource_id"]

    web_data = self.services.web_data_service.all(parent_resource_type, web_data_type, parent_resource_id)
    count = len(web_data)

    # TODO(SN-1040): In future should properly paginate but for now not envisioning having 1000s of individual items
    return PaginationJsonBuilder(
      count=count,
      data=[WebDataJsonBuilder(web_data_singular) for web_data_singular in web_data],
      before=None,
      after=None,
    )
