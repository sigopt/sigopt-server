# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from dataclasses import dataclass

from zigopt.client.model import Client
from zigopt.membership.model import Membership
from zigopt.organization.model import Organization
from zigopt.permission.model import Permission
from zigopt.token.model import Token
from zigopt.user.model import User


@dataclass(frozen=True)
class ClientAuthenticationResult:
  client: Client
  permission: Permission | None = None


@dataclass(frozen=True)
class OrganizationAuthenticationResult:
  membership: Membership
  organization: Organization | None = None


@dataclass(frozen=True)
class AuthenticationResult:
  authenticated_from_email_link: bool = False
  session_expiration: int | None = None
  token: Token | None = None
  user: User | None = None
  organization_authentication_result: OrganizationAuthenticationResult | None = None
  client_authentication_result: ClientAuthenticationResult | None = None
