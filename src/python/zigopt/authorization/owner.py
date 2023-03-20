# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.authorization.client_user import _BaseClientUserAuthorization
from zigopt.client.model import Client
from zigopt.experiment.model import Experiment
from zigopt.membership.model import Membership


class OrganizationOwnerAuthorization(_BaseClientUserAuthorization):
  @classmethod
  def construct_from_user_authorization(cls, user_authorization, current_client, client_token, current_membership):
    assert user_authorization.current_user.id == current_membership.user_id
    return cls(
      current_client=current_client,
      current_user=user_authorization.current_user,
      client_token=client_token,
      current_membership=current_membership,
      user_authorization=user_authorization,
    )

  def __init__(self, current_client, current_user, client_token, current_membership, user_authorization):
    assert isinstance(current_membership, Membership)
    assert current_membership.is_owner
    assert current_membership.organization_id == current_client.organization_id
    assert current_membership.user_id == current_user.id
    super().__init__(
      current_client=current_client,
      current_user=current_user,
      client_token=client_token,
      current_membership=current_membership,
      user_authorization=user_authorization,
    )
    self._client_token = client_token
    self._current_client = current_client

  # NOTE: owner methods take requested_permission to conform to function signature, but never use it because
  # being an owner implies all permissions (for children-clients)

  def can_act_on_client(self, services, requested_permission, client):
    return (
      client.organization_id == self._current_membership.organization_id
      and self._user_authorization.can_act_on_client(services, requested_permission, client)
    )

  def can_act_on_organization(self, services, requested_permission, organization):
    return (
      organization.id == self._current_membership.organization_id
      and self._user_authorization.can_act_on_organization(services, requested_permission, organization)
    )

  def _can_act_on_client_artifacts(self, services, requested_permission, client_id, owner_id_for_artifacts):
    client = services.client_service.find_by_id(client_id)
    if client is None:
      return False
    return (
      self.can_act_on_client(services, requested_permission, client)
      and
      # TODO(SN-1072): This double fetches the client object, but hard to unwind without being positive we are making
      # all the necessary user authorization checks
      # pylint: disable=protected-access
      self._user_authorization._can_act_on_client_artifacts(
        services,
        requested_permission,
        client_id,
        owner_id_for_artifacts,
      )
      # pylint: enable=protected-access
    )

  def filter_can_act_on_experiments(self, services, requested_permission, experiments):
    # TODO(SN-1073): Ideally we would be calling into _can_act_on_client_artifacts here, but it would trigger a bunch
    # of client fetches that we do not need to do
    if not experiments:
      return []
    experiment_ids = [e.id for e in experiments]
    actionable_experiment_ids = {
      e_id
      for (e_id,) in services.database_service.all(
        services.database_service.query(Experiment.id)
        .join(Client)
        .filter(Client.organization_id == self._current_membership.organization_id)
        .filter(Experiment.id.in_(experiment_ids))
      )
    }
    return [e for e in experiments if e.id in actionable_experiment_ids]
