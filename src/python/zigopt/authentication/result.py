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
  authenticated_from_email_link: bool | None
  client: Client | None
  membership: Membership | None
  organization: Organization | None
  permission: Permission | None
  session_expiration: int | None
  token: Token | None
  user: User | None
