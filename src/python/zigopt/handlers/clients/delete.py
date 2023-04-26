# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import user_token_authentication
from zigopt.handlers.clients.base import ClientHandler
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.net.errors import ForbiddenError


class ClientsDeleteHandler(ClientHandler):
  authenticator = user_token_authentication

  def handle(self):
    assert self.auth is not None
    assert self.client is not None

    user_can_delete = self.services.membership_service.user_is_owner_for_organization(
      user_id=self.auth.current_user.id,
      organization_id=self.client.organization_id,
    )
    if user_can_delete:
      self.do_delete()
      return {}
    raise ForbiddenError("You cannot delete this client.")

  def do_delete(self):
    assert self.auth is not None
    assert self.client is not None

    self.services.client_service.delete_clients_and_artifacts([self.client])

    self.services.invite_service.delete_stray_invites_by_organization(self.client.organization_id)

    # NOTE: If organization only has one client, then delete. Else, do nothing
    if self.services.client_service.count_by_organization_id(self.client.organization_id) == 0:
      self.services.organization_service.delete_by_id(self.client.organization_id)
    self.services.iam_logging_service.log_iam(
      requestor=self.auth.current_user,
      event_name=IamEvent.CLIENT_DELETE,
      request_parameters={"client_id": self.client.id},
      response_element={},
      response_status=IamResponseStatus.SUCCESS,
    )
    return {}
