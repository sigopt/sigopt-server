# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import TypedDict

from zigopt.client.model import Client
from zigopt.membership.model import Membership
from zigopt.organization.model import Organization
from zigopt.permission.model import Permission
from zigopt.token.model import Token
from zigopt.user.model import User


class authentication_result(TypedDict, total=False):
  authenticated_from_email_link: bool
  client: Client
  membership: Membership
  organization: Organization
  permission: Permission
  session_expiration: int
  token: Token
  user: User
