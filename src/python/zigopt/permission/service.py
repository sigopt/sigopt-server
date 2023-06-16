# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Sequence

from zigopt.common import *
from zigopt.client.model import Client
from zigopt.db.column import JsonPath, jsonb_set, unwind_json_path
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.invite.constant import ADMIN_ROLE, READ_ONLY_ROLE, USER_ROLE
from zigopt.json.builder import PermissionJsonBuilder
from zigopt.membership.model import Membership
from zigopt.net.errors import NotFoundError
from zigopt.permission.model import Permission, PermissionMetaProxy
from zigopt.protobuf.gen.permission.permissionmeta_pb2 import PermissionMeta
from zigopt.services.base import Service
from zigopt.user.model import User


class PermissionService(Service):
  def find_by_user_id(self, user_id: int) -> Sequence[Permission]:
    return self.services.database_service.all(
      self.services.database_service.query(Permission).filter_by(user_id=user_id),
    )

  def find_by_user_ids(self, user_ids: Sequence[int]) -> Sequence[Permission]:
    if not user_ids:
      return []
    return self.services.database_service.all(
      self.services.database_service.query(Permission).filter(Permission.user_id.in_(user_ids)),
    )

  def find_by_client_id(self, client_id: int) -> Sequence[Permission]:
    return self.services.database_service.all(
      self.services.database_service.query(Permission).filter_by(client_id=client_id),
    )

  def find_by_organization_id(self, organization_id: int) -> Sequence[Permission]:
    clients = self.services.client_service.find_by_organization_id(organization_id)
    if not clients:
      return []
    return self.services.database_service.all(
      self.services.database_service.query(Permission).filter(Permission.client_id.in_([c.id for c in clients])),
    )

  def find_by_user_and_organization_ids(self, user_id: int, organization_ids: Sequence[int]) -> Sequence[Permission]:
    clients = self.services.client_service.find_by_organization_ids(organization_ids)
    if not clients:
      return []
    return self.services.database_service.all(
      self.services.database_service.query(Permission)
      .filter(Permission.user_id == user_id)
      .filter(Permission.client_id.in_([c.id for c in clients])),
    )

  def find_by_users_and_organizations(
    self, user_ids: Sequence[int], organization_ids: Sequence[int]
  ) -> Sequence[Permission]:
    if not user_ids or not organization_ids:
      return []
    return self.services.database_service.all(
      self.services.database_service.query(Permission)
      .join(Client)
      .filter(Permission.user_id.in_(user_ids))
      .filter(Client.organization_id.in_(organization_ids)),
    )

  def find_by_membership(self, membership: Membership) -> Sequence[Permission]:
    return self.services.database_service.all(
      self.services.database_service.query(Permission)
      .filter(Permission.user_id == membership.user_id)
      .filter(Permission.organization_id == membership.organization_id)
    )

  def count_by_organization_id(self, organization_id: int) -> int:
    return self.services.database_service.count(
      self.services.database_service.query(Permission).join(Client).filter(Client.organization_id == organization_id)
    )

  def count_by_organization_and_user(self, organization_id: int, user_id: int) -> int:
    return self.services.database_service.count(
      self.services.database_service.query(Permission)
      .join(Client)
      .filter(Client.organization_id == organization_id)
      .filter(Permission.user_id == user_id)
    )

  def find_by_client_and_user(self, client_id: int, user_id: int) -> Permission | None:
    return self.services.database_service.one_or_none(
      self.services.database_service.query(Permission).filter_by(client_id=client_id).filter_by(user_id=user_id),
    )

  def delete_by_client_and_user(self, client_id: int, user_id: int) -> int:
    return self.services.database_service.delete_one_or_none(
      self.services.database_service.query(Permission).filter_by(client_id=client_id).filter_by(user_id=user_id),
    )

  def delete_by_organization_and_user(self, organization_id: int, user_id: int) -> int:
    return self.services.database_service.delete(
      self.services.database_service.query(Permission)
      .filter_by(organization_id=organization_id)
      .filter_by(user_id=user_id),
    )

  def set_permission_meta(
    self,
    permission: Permission | None,
    can_admin: bool,
    can_write: bool,
    can_read: bool,
    can_see_experiments_by_others: bool,
  ) -> PermissionMeta:
    meta = PermissionMeta()
    meta.can_admin = coalesce(can_admin, permission and permission.can_admin) or False
    meta.can_write = coalesce(can_write, permission and permission.can_write) or False
    meta.can_read = coalesce(can_read, permission and permission.can_read) or False
    meta.can_see_experiments_by_others = (
      coalesce(
        can_see_experiments_by_others,
        permission and permission.can_see_experiments_by_others,
      )
      or False
    )
    return meta

  def migrate_client(self, permission: Permission, new_client_id: int) -> None:
    old_client_id = permission.client_id
    client_permissions = self.find_by_client_id(new_client_id)
    new_client = self.services.client_service.find_by_id(new_client_id)
    if not new_client:
      raise NotFoundError(f"Client {new_client_id} was not found")

    user_already_exists = any(p.user_id == permission.user_id for p in client_permissions)
    if not user_already_exists:
      self.services.membership_service.create_if_not_exists(
        user_id=permission.user_id,
        organization_id=new_client.organization_id,
      )
      permission.client_id = new_client.id
      permission.organization_id = new_client.organization_id
      self.services.database_service.upsert(permission)

    # Delete the old permission if it still exists
    self.delete_by_client_and_user(old_client_id, permission.user_id)

  def upsert(
    self,
    client: Client,
    user: User,
    can_admin: bool,
    can_write: bool,
    can_read: bool,
    requestor: User,
    role_for_logging: str,
  ) -> Permission:
    membership = self.services.membership_service.find_by_user_and_organization(
      user_id=user.id,
      organization_id=client.organization_id,
    )
    if membership is None:
      raise ValueError("Permission cannot be created without a membership.")
    if user and user.id and client and client.id:
      client_permissions = self.find_by_client_id(client.id)
      permission = find(client_permissions, lambda p: p.user_id == user.id)
      can_see_experiments_by_others = can_admin or client.allow_users_to_see_experiments_by_others
      meta = self.set_permission_meta(permission, can_admin, can_write, can_read, can_see_experiments_by_others)
      if permission:
        self.update_meta(permission, meta)
        iam_event_name = IamEvent.PERMISSION_UPDATE
      else:
        permission = Permission(
          user_id=user.id, client_id=client.id, organization_id=client.organization_id, permission_meta=meta
        )
        self.services.database_service.insert(permission)
        iam_event_name = IamEvent.PERMISSION_CREATE

      self.services.iam_logging_service.log_iam(
        requestor=requestor,
        event_name=iam_event_name,
        request_parameters={
          "user_id": user.id,
          "client_id": client.id,
          "permission": role_for_logging,
        },
        response_element=PermissionJsonBuilder.json(permission, client, user),
        response_status=IamResponseStatus.SUCCESS,
      )

      return permission
    raise ValueError(
      "Cannot create a permission without both a user and a client."
      f" User: {user and user.id}, client: {client and client.id}"
    )

  def upsert_from_role(self, invite_role: str, client: Client, user: User, requestor: User) -> Permission:
    if invite_role == ADMIN_ROLE:
      return self.upsert(
        client,
        user,
        can_admin=True,
        can_write=True,
        can_read=True,
        requestor=requestor,
        role_for_logging=invite_role,
      )
    if invite_role == USER_ROLE:
      return self.upsert(
        client,
        user,
        can_admin=False,
        can_write=True,
        can_read=True,
        requestor=requestor,
        role_for_logging=invite_role,
      )
    if invite_role == READ_ONLY_ROLE:
      return self.upsert(
        client,
        user,
        can_admin=False,
        can_write=False,
        can_read=True,
        requestor=requestor,
        role_for_logging=invite_role,
      )
    raise Exception(f"Unrecognized invite role: {invite_role}\n")

  def update_meta(self, permission: Permission, meta: PermissionMeta) -> int:
    permission.permission_meta = PermissionMetaProxy(meta)
    return self.services.database_service.update_one(
      self.services.database_service.query(Permission).filter(Permission.id == permission.id),
      {Permission.permission_meta: meta},
    )

  def update_privacy_for_client(self, client: Client) -> int:
    meta_clause = Permission.permission_meta
    path = JsonPath(*unwind_json_path(meta_clause.can_see_experiments_by_others))
    meta_clause = jsonb_set(meta_clause, path, client.allow_users_to_see_experiments_by_others)
    return self.services.database_service.update(
      self.services.database_service.query(Permission)
      .filter(~Permission.permission_meta.can_admin)
      .filter(Permission.client_id == client.id),
      {Permission.permission_meta: meta_clause},
    )
