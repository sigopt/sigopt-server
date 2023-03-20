# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.clients.base import ClientHandler
from zigopt.json.builder import ClientJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class ClientsDetailHandler(ClientHandler):
  authenticator = api_token_authentication
  allow_development = True
  required_permissions = READ

  def handle(self):
    return ClientJsonBuilder.json(self.client)
