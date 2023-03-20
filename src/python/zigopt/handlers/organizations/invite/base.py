# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.organizations.base import OrganizationHandler


class OrganizationsInviteHandler(OrganizationHandler):
  def __init__(self, services, request, organization_id, invite_id):
    super().__init__(services, request, organization_id)
    if invite_id is None:
      raise Exception("Invite id required")

    self.invite_id = invite_id
    self.invite = None
    self.pending_permissions = None

  def find_objects(self):
    return extend_dict(
      super().find_objects(),
      {
        "invite": self.services.invite_service.find_by_id(self.invite_id),
        "pending_permissions": self.services.pending_permission_service.find_by_invite_id(self.invite_id),
      },
    )

  def can_act_on_objects(self, requested_permission, objects):
    invite = objects["invite"]
    pending_permissions = objects["pending_permissions"]
    return (
      super().can_act_on_objects(requested_permission, objects)
      and invite.organization_id == self.organization_id
      and all((p.organization_id == self.organization_id for p in pending_permissions))
    )
