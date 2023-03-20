# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.protobuf.gen.token.tokenmeta_pb2 import TokenMeta


class PermissionType(object):
  WRITE = "write"
  READ = "read"
  ADMIN = "admin"


class TokenType(object):
  USER = "user"
  CLIENT_DEV = "client-dev"
  CLIENT_API = "client-api"
  GUEST = "guest"


ALL_TOKEN_TYPES = (
  TokenType.USER,
  TokenType.CLIENT_DEV,
  TokenType.CLIENT_API,
  TokenType.GUEST,
)

_, TOKEN_SCOPE_TO_NAME = generate_constant_map_and_inverse(
  {
    "all_endpoints": TokenMeta.ALL_ENDPOINTS,
    "shared_experiment": TokenMeta.SHARED_EXPERIMENT_SCOPE,
    "signup": TokenMeta.SIGNUP_SCOPE,
  }
)
