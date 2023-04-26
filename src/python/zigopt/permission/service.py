# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.client.model import Client
from zigopt.db.column import JsonPath, jsonb_set, unwind_json_path
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.invite.constant import ADMIN_ROLE, READ_ONLY_ROLE, USER_ROLE
from zigopt.json.builder import PermissionJsonBuilder
from zigopt.permission.model import Permission
from zigopt.protobuf.gen.permission.permissionmeta_pb2 import PermissionMeta
from zigopt.services.base import Service


class PermissionService(Service):
  def find_by_user_id(self, user_id):
    return self.services.database_service.all(
      self.services.database_service.query(Permission).filter_by(user_id=user_id),
    )

  def find_by_user_ids(self, user_ids):
    if not user_ids:
      return []
    return self.services.database_service.all(
      self.services.database_service.query(Permission).filter(Permission.user_id.in_(user_ids)),
    )

  def find_by_client_id(self, client_id):
    return self.services.database_service.all(
      self.services.database_service.query(Permission).filter_by(client_id=client_id),
    )

  def find_by_organization_id(self, organization_id):
    clients = self.services.client_service.find_by_organization_id(organization_id)
    if not clients:
      return []
    return self.services.database_service.all(
      self.services.database_service.query(Permission).filter(Permission.client_id.in_([c.id for c in clients])),
    )

  def find_by_user_and_organization_ids(self, user_id, organization_ids):
    clients = self.services.client_service.find_by_organization_ids(organization_ids)
    if not clients:
      return []
    return self.services.database_service.all(
      self.services.database_service.query(Permission)
      .filter(Permission.user_id == user_id)
      .filter(Permission.client_id.in_([c.id for c in clients])),
    )

  def find_by_users_and_organizations(self, user_ids, organization_ids):
    if not user_ids or not organization_ids:
      return []
    return self.services.database_service.all(
      self.services.database_service.query(Permission)
      .join(Client)
      .filter(Permission.user_id.in_(user_ids))
      .filter(Client.organization_id.in_(organization_ids)),
    )

  def find_by_membership(self, membership):
    return self.services.database_service.all(
      self.services.database_service.query(Permission)
      .filter(Permission.user_id == membership.user_id)
      .filter(Permission.organization_id == membership.organization_id)
    )

  def count_by_organization_id(self, organization_id):
    return self.services.database_service.count(
      self.services.database_service.query(Permission).join(Client).filter(Client.organization_id == organization_id)
    )

  def count_by_organization_and_user(self, organization_id, user_id):
    return self.services.database_service.count(
      self.services.database_service.query(Permission)
      .join(Client)
      .filter(Client.organization_id == organization_id)
      .filter(Permission.user_id == user_id)
    )

  def find_by_client_and_user(self, client_id, user_id):
    return self.services.database_service.one_or_none(
      self.services.database_service.query(Permission).filter_by(client_id=client_id).filter_by(user_id=user_id),
    )

  def delete_by_client_and_user(self, client_id, user_id):
    return self.services.database_service.delete_one_or_none(
      self.services.database_service.query(Permission).filter_by(client_id=client_id).filter_by(user_id=user_id),
    )

  def delete_by_organization_and_user(self, organization_id, user_id):
    return self.services.database_service.delete(
      self.services.database_service.query(Permission)
      .filter_by(organization_id=organization_id)
      .filter_by(user_id=user_id),
    )

  def set_permission_meta(self, permission, can_admin, can_write, can_read, can_see_experiments_by_others):
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

  def migrate_client(self, permission, new_client_id):
    old_client_id = permission.client_id
    client_permissions = self.find_by_client_id(new_client_id)
    new_client = self.services.client_service.find_by_id(new_client_id)

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

  def upsert(self, client, user, can_admin, can_write, can_read, requestor, role_for_logging):
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

  def upsert_from_role(self, invite_role, client, user, requestor):
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

  def update_meta(self, permission, meta):
    permission.permission_meta = meta
    return self.services.database_service.update_one(
      self.services.database_service.query(Permission).filter(Permission.id == permission.id),
      {Permission.permission_meta: meta},
    )

  def update_privacy_for_client(self, client):
    meta_clause = Permission.permission_meta
    path = JsonPath(*unwind_json_path(meta_clause.can_see_experiments_by_others))
    meta_clause = jsonb_set(meta_clause, path, client.allow_users_to_see_experiments_by_others)
    return self.services.database_service.update(
      self.services.database_service.query(Permission)
      .filter(~Permission.permission_meta.can_admin)
      .filter(Permission.client_id == client.id),
      {Permission.permission_meta: meta_clause},
    )
