# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections.abc import Sequence

from sqlalchemy import or_
from sqlalchemy.orm import Query

from zigopt.common import *
from zigopt.client.model import Client
from zigopt.membership.model import Membership
from zigopt.permission.model import Permission
from zigopt.protobuf.gen.client.clientmeta_pb2 import ClientMeta
from zigopt.protobuf.lib import copy_protobuf
from zigopt.services.base import Service
from zigopt.token.model import Token
from zigopt.user.model import User


class ClientService(Service):
  def find_by_id(
    self, client_id: int, include_deleted: bool = False, current_client: Client | None = None
  ) -> Client | None:
    if current_client and current_client.id == client_id:
      if not include_deleted and current_client.deleted:
        return None
      return current_client
    return self.services.database_service.one_or_none(
      self._include_deleted_clause(
        include_deleted,
        self.services.database_service.query(Client).filter(Client.id == client_id),
      )
    )

  def find_by_ids(self, client_ids: Sequence[int], include_deleted: bool = False) -> Sequence[Client]:
    if client_ids:
      return self.services.database_service.all(
        self._include_deleted_clause(
          include_deleted,
          self.services.database_service.query(Client).filter(Client.id.in_(client_ids)),
        ),
      )
    return []

  def find_by_organization_id(self, organization_id: int, include_deleted: bool = False) -> Sequence[Client]:
    return self.services.database_service.all(
      self._include_deleted_clause(
        include_deleted,
        self.services.database_service.query(Client).filter(Client.organization_id == organization_id),
      ),
    )

  def find_by_organization_ids(
    self, organization_ids: Sequence[int], include_deleted: bool = False
  ) -> Sequence[Client]:
    if organization_ids:
      return self.services.database_service.all(
        self._include_deleted_clause(
          include_deleted,
          self.services.database_service.query(Client).filter(Client.organization_id.in_(organization_ids)),
        ),
      )
    return []

  def find_by_ids_or_organization_ids(
    self, client_ids: Sequence[int], organization_ids: Sequence[int], include_deleted: bool = False
  ) -> Sequence[Client]:
    if not organization_ids:
      return self.find_by_ids(client_ids, include_deleted)
    if not client_ids:
      return self.find_by_organization_ids(organization_ids, include_deleted)
    return self.services.database_service.all(
      self._include_deleted_clause(
        include_deleted,
        self.services.database_service.query(Client).filter(
          or_(
            Client.id.in_(client_ids),
            Client.organization_id.in_(organization_ids),
          )
        ),
      )
    )

  def count_by_organization_id(self, organization_id: int, include_deleted: bool = False) -> int:
    return self.services.database_service.count(
      self._include_deleted_clause(
        include_deleted,
        self.services.database_service.query(Client).filter(Client.organization_id == organization_id),
      )
    )

  def _include_deleted_clause(self, include_deleted: bool, q: Query) -> Query:
    if not include_deleted:
      return q.filter(~Client.client_meta.deleted)
    return q

  def insert(self, client: Client) -> Client:
    self.services.database_service.insert(client)
    self.services.database_service.flush_session()
    return client

  def update_security(self, client: Client, allow_users_to_see_experiments_by_others: bool) -> Client:
    meta = copy_protobuf(client.client_meta) if client.client_meta else ClientMeta()
    meta.client_security.allow_users_to_see_experiments_by_others = allow_users_to_see_experiments_by_others

    self.services.database_service.update_one(
      self.services.database_service.query(Client).filter_by(id=client.id),
      {Client.client_meta: meta},
    )
    client.client_meta = meta

    return client

  def delete(self, client: Client) -> None:
    """
        Not a true DB delete, just sets the deleted flag.
        There's a race condition here... not a big deal if we are deleting though.
        """
    new_meta = copy_protobuf(client.client_meta) if client.client_meta else ClientMeta()
    new_meta.deleted = True
    client.client_meta = new_meta
    self.services.database_service.upsert(client)

  def delete_clients_and_artifacts(self, clients: Sequence[Client]) -> None:
    client_ids = [client.id for client in clients]

    self.services.database_service.delete(
      self.services.database_service.query(Token).filter(Token.client_id.in_(client_ids))
    )

    self.services.pending_permission_service.delete_by_client_ids(client_ids)

    self.services.database_service.delete(
      self.services.database_service.query(Permission).filter(Permission.client_id.in_(client_ids))
    )

    self.services.experiment_service.delete_by_client_ids(client_ids)

    for client in clients:
      self.services.client_service.delete(client)

  def find_clients_in_organizations_visible_to_user(
    self, user: User, memberships: Sequence[Membership]
  ) -> Sequence[Client]:
    assert all(m.user_id == user.id for m in memberships)
    organizations = [
      org
      for org in self.services.organization_service.find_by_ids([m.organization_id for m in memberships])
      if self.services.invite_service.can_have_membership_to_organization(user=user, organization=org)
    ]
    org_ids = {o.id for o in organizations}
    memberships = [m for m in memberships if m.organization_id in org_ids]
    owner_memberships, member_memberships = partition(memberships, lambda m: m.is_owner)
    clients: list[Client] = []
    if owner_memberships:
      clients.extend(self.find_by_organization_ids(organization_ids=[m.organization_id for m in owner_memberships]))
    if member_memberships:
      permissions = self.services.permission_service.find_by_user_and_organization_ids(
        user_id=user.id,
        organization_ids=[m.organization_id for m in member_memberships],
      )
      clients.extend(self.find_by_ids(client_ids=[p.client_id for p in permissions]))
    return clients
