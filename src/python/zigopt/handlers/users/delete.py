# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.users.base import UserHandler
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.invite.model import Invite
from zigopt.net.errors import BadParamError, ForbiddenError
from zigopt.permission.model import Permission
from zigopt.token.model import Token
from zigopt.user.model import do_password_hash_work_factor_update, password_matches


class UsersDeleteHandler(UserHandler):
  authenticator = api_token_authentication

  def parse_params(self, request):
    return request.optional_param("password")

  def handle(self, password):  # type: ignore
    assert self.auth is not None
    assert self.user is not None

    self.ensure_no_orphaned_organizations()
    self.ensure_no_orphaned_clients()

    if validated_request := password and password_matches(password, self.user.hashed_password):
      do_password_hash_work_factor_update(self.services, self.user, password)
    if validated_request:
      self.do_delete()
      self.services.iam_logging_service.log_iam(
        requestor=self.auth.current_user,
        event_name=IamEvent.USER_DELETE,
        request_parameters={
          "user_id": self.user.id,
        },
        response_element={},
        response_status=IamResponseStatus.SUCCESS,
      )
      return {}
    raise BadParamError("Invalid password")

  def ensure_no_orphaned_organizations(self):
    assert self.user is not None

    owner_memberships = self.services.membership_service.find_owners_by_user_id(self.user.id)
    organization_ids = set(m.organization_id for m in owner_memberships)
    if not organization_ids:
      return

    other_owner_memberships = self.services.membership_service.organizations_with_other_owners(
      list(organization_ids), self.user.id
    )
    still_owned_organization_ids = set(m.organization_id for m in other_owner_memberships)

    if unowned_organization_ids := organization_ids - still_owned_organization_ids:
      other_non_owner_memberships = self.services.membership_service.organizations_with_other_non_owners(
        list(unowned_organization_ids),
        self.user.id,
      )
      if orphaned_organization_ids := set(m.organization_id for m in other_non_owner_memberships):
        raise ForbiddenError(
          "This user cannot be deleted without assigning another owner or removing "
          f"all other users from the following organizations: {orphaned_organization_ids}"
        )

  def ensure_no_orphaned_clients(self):
    assert self.user is not None

    permissions = self.services.database_service.all(
      self.services.database_service.query(Permission).filter(Permission.user_id == self.user.id)
    )

    organization_ids = set(p.organization_id for p in permissions)
    organizations_with_other_owners = self.services.membership_service.organizations_with_other_owners(
      list(organization_ids),
      self.user.id,
    )
    other_owned_organizations = set(m.organization_id for m in organizations_with_other_owners)

    if client_ids := [p.client_id for p in permissions if p.organization_id not in other_owned_organizations]:
      outstanding_permissions = self.services.database_service.all(
        self.services.database_service.query(Permission)
        .filter(Permission.client_id.in_(client_ids))
        .filter(Permission.user_id != self.user.id)
      )
      outstanding_client_ids = [p.client_id for p in outstanding_permissions]

      if orphaned_clients := list(set(client_ids) - set(outstanding_client_ids)):
        raise ForbiddenError(f"This user cannot be deleted without deleting the following clients: {orphaned_clients}")

  def do_delete(self):
    assert self.user is not None

    self.services.database_service.delete(
      self.services.database_service.query(Permission).filter(Permission.user_id == self.user.id)
    )

    self.services.membership_service.delete_by_user_id(self.user.id)

    # NOTE: 13/10/2017 deleting a membership should cascade and delete these other
    # artefacts automatically in the future
    self.services.database_service.delete(
      self.services.database_service.query(Invite).filter(Invite.inviter == self.user.id)
    )

    self.services.database_service.delete(
      self.services.database_service.query(Token).filter(Token.user_id == self.user.id)
    )

    self.services.user_service.delete(self.user)
