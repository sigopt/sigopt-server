# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.authorization.constant import AuthorizationDenied
from zigopt.authorization.empty import EmptyAuthorization
from zigopt.client.model import Client
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, READ, WRITE


class UserAuthorization(EmptyAuthorization):
  def __init__(self, current_user, user_token, scoped_membership, scoped_permission):
    super().__init__()
    self._current_user = current_user
    self._user_token = user_token
    self.scoped_membership = scoped_membership
    self.scoped_permission = scoped_permission

  @property
  def api_token(self):
    return self._user_token

  @property
  def current_user(self):
    return self._current_user

  def can_act_on_user(self, services, requested_permission, user):
    if user:
      if self.current_user.id == user.id:
        return True
      if requested_permission == READ:
        # TODO: Should we be using scoped membership here? It is safe if we don't, but might speed things up
        if services.membership_service.users_are_mutually_visible(
          user1_id=self.current_user.id,
          user2_id=user.id,
        ):
          return True
        user_ids = (user.id, self.current_user.id)
        permissions = services.permission_service.find_by_user_ids(user_ids)
        if any(p1.client_id == p2.client_id and p1.user_id != p2.user_id for p1 in permissions for p2 in permissions):
          return True
    return False

  def _infer_organization_id_from_client_id(self, services, client_id):
    # NOTE: If we have previously fetched the permission, we can short-circuit the client fetch
    if self.scoped_permission and self.scoped_permission.client_id == client_id:
      return self.scoped_permission.organization_id
    client: Client | None = services.client_service.find_by_id(client_id)
    return napply(client, lambda c: c.organization_id)

  def _infer_organization_from_organization_id(self, services, organization_id):
    return services.organization_service.find_by_id(organization_id)

  def can_act_on_client(self, services, requested_permission, client):
    if client:
      return self.can_act_on_client_id(
        services,
        requested_permission,
        client.id,
        organization_id=client.organization_id,
      )
    return False

  def can_act_on_client_id(self, services, requested_permission, client_id, organization_id=None):
    if client_id:
      organization_id = organization_id or self._infer_organization_id_from_client_id(services, client_id)
      organization = self._infer_organization_from_organization_id(services, organization_id)
      membership = self._membership(services, organization=organization)
      if membership:
        if membership.is_owner:
          return True
        p = self._permission(services, client_id)
        return self.compare_permissions(p, requested_permission)
      return self._no_membership_status(services)
    return False

  def can_act_on_organization(self, services, requested_permission, organization):
    if organization:
      membership = self._membership(services, organization=organization)
      if not membership:
        return self._no_membership_status(services)
      if requested_permission == READ:
        return True
      if requested_permission in (WRITE, ADMIN):
        return membership.is_owner
    return False

  def _can_act_on_client_artifacts(self, services, requested_permission, client_id, owner_id_for_artifacts):
    organization_id = self._infer_organization_id_from_client_id(services, client_id)
    if organization_id:
      organization = self._infer_organization_from_organization_id(services, organization_id)
      membership = self._membership(services, organization=organization)
      if membership:
        if membership.is_owner:
          return True

        p = self._permission(services, client_id)
        if not p:
          return False

        if p.can_see_experiments_by_others or self._current_user.id == owner_id_for_artifacts:
          return self.compare_permissions(p, requested_permission)
      return self._no_membership_status(services)
    return False

  def can_act_on_token(self, services, requested_permission, token):
    return bool(token and self.current_user.id in {token.user_id, token.creating_user_id})

  def _no_membership_status(self, services):
    if self.current_user and not services.email_verification_service.has_verified_email_if_needed(self.current_user):
      return AuthorizationDenied.NEEDS_EMAIL_VERIFICATION
    return False

  def compare_permissions(self, current_permission, requested_permission):
    if requested_permission == READ:
      return bool(current_permission and current_permission.can_read)
    if requested_permission == WRITE:
      return bool(current_permission and current_permission.can_write)
    if requested_permission == ADMIN:
      return bool(current_permission and current_permission.can_admin)
    return False

  def _membership(self, services, organization):
    if organization:
      if services.invite_service.can_have_membership_to_organization(
        user=self.current_user,
        organization=organization,
      ):
        if self.scoped_membership:
          assert self.scoped_membership.user_id == self.current_user.id
          if self.scoped_membership.organization_id == organization.id:
            return self.scoped_membership
          return None
        return services.membership_service.find_by_user_and_organization(
          user_id=self.current_user.id,
          organization_id=organization.id,
        )
    return None

  def _permission(self, services, client_id):
    if client_id:
      if self.scoped_permission:
        assert self.scoped_permission.user_id == self.current_user.id
        if self.scoped_permission.client_id == client_id:
          return self.scoped_permission
        return None
      return services.permission_service.find_by_client_and_user(client_id=client_id, user_id=self.current_user.id)
    return None


class UserLoginAuthorization(UserAuthorization):
  def __init__(self, current_user, user_token, authenticated_from_email_link):
    super().__init__(
      current_user=current_user,
      user_token=user_token,
      scoped_membership=None,
      scoped_permission=None,
    )
    self._authenticated_from_email_link = authenticated_from_email_link

  @property
  def authenticated_from_email_link(self):
    return self._authenticated_from_email_link
