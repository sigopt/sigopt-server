# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.brand.constant import PRODUCT_NAME, PYTHON_CLIENT_URL
from zigopt.handlers.base.handler import Handler
from zigopt.protobuf.gen.token.tokenmeta_pb2 import NONE


class WelcomeHandler(Handler):
  authenticator = api_token_authentication
  required_permissions = NONE

  def handle(self):
    app_url = self.services.config_broker["address.app_url"]
    message = (
      f"Welcome to the {PRODUCT_NAME} API!"
      f" You can view our API docs at {app_url}/docs."
      f" Try using our official python client at {PYTHON_CLIENT_URL}"
    )
    return {"message": message}
