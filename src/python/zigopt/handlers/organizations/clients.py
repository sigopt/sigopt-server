# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication, user_token_authentication
from zigopt.client.model import Client
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.organizations.base import OrganizationHandler
from zigopt.handlers.validate.client import validate_client_name
from zigopt.handlers.validate.validate_dict import ValidationType, get_with_validation
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.json.builder import ClientJsonBuilder, PaginationJsonBuilder
from zigopt.protobuf.gen.client.clientmeta_pb2 import ClientMeta
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, READ


class OrganizationsClientsListDetailHandler(OrganizationHandler):
  authenticator = user_token_authentication
  required_permissions = READ

  def handle(self):  # type: ignore
    assert self.auth is not None
    assert self.organization is not None

    membership = self.services.membership_service.find_by_user_and_organization(
      user_id=self.auth.current_user.id,
      organization_id=self.organization.id,
    )
    clients = self.services.client_service.find_clients_in_organizations_visible_to_user(
      user=self.auth.current_user,
      memberships=remove_nones_sequence([membership]),
    )

    return PaginationJsonBuilder(data=[ClientJsonBuilder(c) for c in clients])


class OrganizationsClientsCreateHandler(OrganizationHandler):
  authenticator = api_token_authentication
  required_permissions = ADMIN

  Params = ImmutableStruct("Params", ("name",))

  def parse_params(self, request):
    data = request.params()
    name = get_with_validation(data, "name", ValidationType.string)
    name = validate_client_name(name)
    return OrganizationsClientsCreateHandler.Params(name=name)

  def handle(self, params):  # type: ignore
    assert self.auth is not None
    assert self.organization is not None

    meta = ClientMeta()
    meta.date_created = unix_timestamp()

    client = Client(
      organization_id=self.organization.id,
      name=params.name,
      client_meta=meta,
    )
    self.services.client_service.insert(client)
    self.services.project_service.create_example_for_client(client_id=client.id)

    client_json = ClientJsonBuilder.json(client)
    self.services.iam_logging_service.log_iam(
      requestor=self.auth.current_user,
      event_name=IamEvent.CLIENT_CREATE,
      request_parameters={
        "name": client.name,
      },
      response_element=client_json,
      response_status=IamResponseStatus.SUCCESS,
    )
    return client_json
