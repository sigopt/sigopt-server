# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Mapping, Optional, Sequence

from sigopt_config.broker import ConfigBroker

from zigopt.common import *
from zigopt.authorization.empty import EmptyAuthorization
from zigopt.client.model import Client
from zigopt.common.sigopt_datetime import datetime_to_seconds
from zigopt.invite.model import Invite
from zigopt.json.builder.invite_base import BaseInviteJsonBuilder
from zigopt.json.builder.json_builder import JsonBuilderValidationType, ValidationType, field
from zigopt.json.builder.pending_permission import PendingPermissionJsonBuilder
from zigopt.membership.model import MembershipType
from zigopt.organization.model import Organization
from zigopt.permission.pending.model import PendingPermission


class InviteJsonBuilder(BaseInviteJsonBuilder):
  object_name = "invite"

  def __init__(
    self,
    auth: EmptyAuthorization,
    config_broker: ConfigBroker,
    invite: Invite,
    pending_permissions: Sequence[PendingPermission],
    organization: Organization,
    client_map: Mapping[int, Client],
  ):
    assert all(pp.organization_id == organization.id for pp in pending_permissions)
    assert invite.organization_id == organization.id
    super().__init__(auth, invite, config_broker)
    self._pending_permissions = pending_permissions
    self._organization = organization
    self._client_map = client_map

  @field(ValidationType.id)
  def id(self) -> int:
    return self._invite.id

  @field(ValidationType.arrayOf(JsonBuilderValidationType()))
  def pending_permissions(self) -> list[PendingPermissionJsonBuilder]:
    return [
      PendingPermissionJsonBuilder(
        self._auth,
        self._config_broker,
        pp,
        self._invite,
        self._client_map[pp.client_id],
      )
      for pp in self._pending_permissions
    ]

  @field(ValidationType.integer)
  def created(self) -> Optional[float]:
    return napply(self._invite.timestamp, datetime_to_seconds)

  @field(ValidationType.enum(MembershipType))
  def membership_type(self) -> Optional[str]:
    membership_type: MembershipType = self._invite.membership_type
    return napply(membership_type, lambda i: i.value)

  @field(ValidationType.id)
  def organization(self) -> int:
    return self._organization.id
