# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import user_token_authentication
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.validate.client import validate_client_name
from zigopt.handlers.validate.validate_dict import ValidationType, get_with_validation
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.json.builder import ClientJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import NONE


class ClientsCreateHandler(Handler):
  authenticator = user_token_authentication
  required_permissions = NONE

  def parse_params(self, request):
    return request.params()

  def handle(self, data):
    assert self.auth is not None

    name = get_with_validation(data, "name", ValidationType.string)
    name = validate_client_name(name)

    client_security = None
    allow_users_to_see_experiments_by_others = True
    if "client_security" in data:
      client_security = get_with_validation(data, "client_security", ValidationType.object)
      allow_users_to_see_experiments_by_others = client_security.get("allow_users_to_see_experiments_by_others")

    (_, client) = self.services.organization_service.set_up_new_organization(
      organization_name=name,
      client_name=name,
      user=self.auth.current_user,
      allow_users_to_see_experiments_by_others=allow_users_to_see_experiments_by_others,
      user_is_owner=True,
      requestor=self.auth.current_user,
    )

    client_json = ClientJsonBuilder.json(client)
    self.services.iam_logging_service.log_iam(
      requestor=self.auth.current_user,
      event_name=IamEvent.CLIENT_CREATE,
      request_parameters={
        "name": name,
        "client_security": client_security,
      },
      response_element=client_json,
      response_status=IamResponseStatus.SUCCESS,
    )
    return client_json
