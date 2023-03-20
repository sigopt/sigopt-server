# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.organizations.invite.base import OrganizationsInviteHandler
from zigopt.handlers.organizations.invite.modify import OrganizationsModifyInviteHandler
from zigopt.json.builder import InviteJsonBuilder


class OrganizationsUpdateInviteHandler(OrganizationsInviteHandler, OrganizationsModifyInviteHandler):
  def handle(self, params):
    email, membership_type, client_invites, client_map = self.unpack_params(params)

    self.check_can_invite(
      email=email,
      client_invites=client_invites,
      client_map=client_map,
      membership_type=membership_type,
      skip_existing=True,
    )

    (invite, pending_permissions) = self.update_invite(
      self.invite,
      self.organization,
      membership_type,
      client_invites,
    )

    return InviteJsonBuilder.json(
      self.auth,
      self.services.config_broker,
      invite,
      pending_permissions,
      self.organization,
      client_map,
    )
