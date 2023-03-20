# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.users.base import UserHandler
from zigopt.json.builder import UserJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class UsersDetailHandler(UserHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self):
    return UserJsonBuilder.json(self.user)
