# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.authorization.client_user import _BaseClientUserAuthorization
from zigopt.permission.model import Permission


class OrganizationMemberAuthorization(_BaseClientUserAuthorization):
  @classmethod
  def construct_from_user_authorization(
    cls,
    user_authorization,
    current_client,
    client_token,
    current_membership,
    current_permission,
  ):
    assert user_authorization.current_user.id == current_permission.user_id
    return cls(
      current_client=current_client,
      current_user=user_authorization.current_user,
      client_token=client_token,
      current_membership=current_membership,
      current_permission=current_permission,
      user_authorization=user_authorization,
    )

  def __init__(
    self,
    current_client,
    current_user,
    client_token,
    current_membership,
    current_permission,
    user_authorization,
  ):
    assert isinstance(current_permission, Permission)
    assert current_permission.client_id == current_client.id
    assert current_permission.user_id == current_user.id
    super().__init__(
      current_client=current_client,
      current_user=current_user,
      client_token=client_token,
      current_membership=current_membership,
      user_authorization=user_authorization,
    )
    self._current_permission = current_permission

  def can_act_on_client(self, services, requested_permission, client):
    if client:
      return self._can_act_on_client_id(services, requested_permission, client.id)
    return False

  def _can_act_on_client_id(self, services, requested_permission, client_id):
    return (
      self._current_permission
      and self._current_permission.client_id == client_id
      and self._user_authorization.can_act_on_client_id(services, requested_permission, client_id)
    )

  def can_act_on_organization(self, services, requested_permission, organization):
    return (
      self._current_permission
      and self._current_permission.organization_id == organization.id
      and self._user_authorization.can_act_on_organization(services, requested_permission, organization)
    )

  def _can_act_on_client_artifacts(self, services, requested_permission, client_id, owner_id_for_artifacts):
    if self._can_act_on_client_id(services, requested_permission, client_id):
      if self._current_permission.can_see_experiments_by_others:
        owner_can_see_this_artifact = client_id == self._current_client.id
      else:
        owner_can_see_this_artifact = (
          owner_id_for_artifacts is not None and owner_id_for_artifacts == self.current_user.id
        )
      return (
        owner_can_see_this_artifact
        and
        # pylint: disable=protected-access
        self._user_authorization._can_act_on_client_artifacts(
          services,
          requested_permission,
          client_id,
          owner_id_for_artifacts,
        )
        # pylint: enable=protected-access
      )
    return False
