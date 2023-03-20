# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.clients.base import ClientHandler
from zigopt.json.builder import PaginationJsonBuilder, TagJsonBuilder
from zigopt.net.errors import BadParamError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ
from zigopt.tag.model import Tag


class ClientsTagsListHandler(ClientHandler):
  sort_by_id_field = "id"
  default_sort_field = sort_by_id_field
  sort_fields = {
    sort_by_id_field: (Tag.id,),
  }
  authenticator = api_token_authentication
  required_permissions = READ

  Params = ImmutableStruct("Params", ["paging", "sort", "Field"])

  def parse_params(self, request):
    paging = request.get_paging()
    sort = request.get_sort(self.default_sort_field, default_ascending=False)
    try:
      Field = self.sort_fields[sort.field]
    except KeyError as e:
      raise BadParamError(f"Invalid sort: {sort.field}") from e
    return self.Params(
      paging=paging,
      sort=sort,
      Field=Field,
    )

  def handle(self, params):
    query = self.services.tag_service.find_by_client_id_query(self.client_id)
    tags, new_before, new_after = self.services.query_pager.fetch_page(
      q=query,
      Field=params.Field,
      paging=params.paging,
      ascending=params.sort.ascending,
    )
    count = self.services.database_service.count(query)
    return PaginationJsonBuilder(
      data=[TagJsonBuilder(tag) for tag in tags],
      count=count,
      before=new_before,
      after=new_after,
    )
