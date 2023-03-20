# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.files.base import FileHandler
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class FileDetailHandler(FileHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self):
    return self.get_file_json_builder()
