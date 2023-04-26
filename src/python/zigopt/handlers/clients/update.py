# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import user_token_authentication
from zigopt.client.model import Client
from zigopt.handlers.clients.base import ClientHandler
from zigopt.handlers.validate.client import validate_client_name
from zigopt.handlers.validate.validate_dict import ValidationType, get_with_validation
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.json.builder import ClientJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN


class ClientsUpdateHandler(ClientHandler):
  authenticator = user_token_authentication
  required_permissions = ADMIN

  def parse_params(self, request):
    data = request.params()
    params = {}
    if "name" in data:
      name = get_with_validation(data, "name", ValidationType.string)
      params["name"] = validate_client_name(name)

    if "client_security" in data:
      client_security = get_with_validation(data, "client_security", ValidationType.object)
      params["client_security"] = client_security

    return params

  def handle(self, params):
    assert self.auth is not None
    assert self.client is not None

    name = params.get("name")
    client_security = params.get("client_security")

    if name is not None:
      self.services.database_service.update_one(
        self.services.database_service.query(Client).filter_by(id=self.client.id),
        {Client.name: name},
      )
      self.client.name = name

    if client_security is not None:
      allow_users_to_see_experiments_by_others = get_with_validation(
        client_security, "allow_users_to_see_experiments_by_others", ValidationType.boolean
      )
      self.client = self.services.client_service.update_security(self.client, allow_users_to_see_experiments_by_others)
      self.services.permission_service.update_privacy_for_client(self.client)

    client_json = ClientJsonBuilder.json(self.client)
    self.services.iam_logging_service.log_iam(
      requestor=self.auth.current_user,
      event_name=IamEvent.CLIENT_UPDATE,
      request_parameters=remove_nones_mapping(
        {
          "name": name,
          "client_security": client_security,
        }
      ),
      response_element=client_json,
      response_status=IamResponseStatus.SUCCESS,
    )
    return client_json
