# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Literal

from zigopt.authorization.empty import EmptyAuthorization  # type: ignore
from zigopt.client.model import Client  # type: ignore
from zigopt.config.broker import ConfigBroker
from zigopt.invite.model import Invite  # type: ignore
from zigopt.json.builder.invite_base import BaseInviteJsonBuilder
from zigopt.json.builder.json_builder import ValidationType, field
from zigopt.permission.pending.model import PendingPermission  # type: ignore


class PendingPermissionJsonBuilder(BaseInviteJsonBuilder):
  object_name = "pending_permission"

  def __init__(
    self,
    auth: EmptyAuthorization,
    config_broker: ConfigBroker,
    pending_permission: PendingPermission,
    invite: Invite,
    client: Client,
  ):
    assert pending_permission.client_id == client.id
    assert invite.organization_id == client.organization_id
    super().__init__(auth, invite, config_broker)
    self._pending_permission = pending_permission
    self._client = client

  @field(ValidationType.id)
  def client(self) -> int:
    return self._pending_permission.client_id

  @field(ValidationType.string)
  def client_name(self) -> str:
    # NOTE: It's a bit weird that we expose client_name as a separate field
    # from client id, instead of just a full client object. But that's to make sure
    # we aren't leaking anything more than we need to. The viewer of this object may
    # not have permission to call /clients/X, so we shouldn't reveal the full client
    # object.
    return self._client.name

  @field(ValidationType.string)
  def role(self) -> Literal["admin", "read-only", "uninvited", "user"]:
    return self._pending_permission.role
