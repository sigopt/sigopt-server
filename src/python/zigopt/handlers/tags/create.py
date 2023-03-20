# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.clients.base import ClientHandler
from zigopt.handlers.validate.base import validate_name
from zigopt.handlers.validate.tag import validate_tag_json_dict_for_create
from zigopt.handlers.validate.validate_dict import ValidationType, get_with_validation
from zigopt.json.builder import TagJsonBuilder
from zigopt.net.errors import ConflictingDataError
from zigopt.protobuf.gen.tag.tagdata_pb2 import TagData
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE
from zigopt.tag.model import Tag
from zigopt.tag.service import TagExistsException


class ClientsTagsCreateHandler(ClientHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  Params = ImmutableStruct(
    "Params",
    [
      "name",
      "color",
    ],
  )

  def parse_params(self, request):
    data = request.params()
    validate_tag_json_dict_for_create(data)
    return self.Params(
      name=validate_name(get_with_validation(data, "name", ValidationType.string)),
      color=get_with_validation(data, "color", ValidationType.color_hex),
    )

  def handle(self, params):
    name = params.name
    tag = Tag(
      name=name,
      client_id=self.client.id,
      data=TagData(color=params.color),
    )
    try:
      inserted_tag = self.services.tag_service.insert(tag)
    except TagExistsException as e:
      raise ConflictingDataError(f"The tag with name `{e.name}` already exists.") from e
    return TagJsonBuilder(inserted_tag)
