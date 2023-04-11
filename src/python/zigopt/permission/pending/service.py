# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.permission.pending.model import PendingPermission
from zigopt.services.base import Service


class PendingPermissionService(Service):
  def create_pending_permission(self, invite, client, role):
    return PendingPermission(
      invite_id=invite.id,
      client_id=client.id,
      organization_id=invite.organization_id,
      role=role,
    )

  def find_by_invite_id(self, invite_id):
    return self.services.database_service.all(
      self.services.database_service.query(PendingPermission).filter(PendingPermission.invite_id == invite_id)
    )

  def find_by_invite_ids(self, invite_ids):
    if invite_ids:
      return self.services.database_service.all(
        self.services.database_service.query(PendingPermission).filter(PendingPermission.invite_id.in_(invite_ids))
      )
    return []

  def count_by_invite_id(self, invite_id):
    return self.services.database_service.count(
      self.services.database_service.query(PendingPermission).filter(PendingPermission.invite_id == invite_id)
    )

  def find_by_client_id(self, client_id):
    return self.services.database_service.all(
      self.services.database_service.query(PendingPermission).filter(PendingPermission.client_id == client_id)
    )

  def find_by_organization_id(self, organization_id):
    return self.services.database_service.all(
      self.services.database_service.query(PendingPermission).filter(
        PendingPermission.organization_id == organization_id
      )
    )

  def insert(self, pending_permission):
    self.services.database_service.insert(pending_permission)
    return pending_permission

  def upsert(self, pending_permission):
    self.services.database_service.upsert(pending_permission)
    return pending_permission

  def delete(self, pending_permission):
    return self.services.database_service.delete_one_or_none(
      self.services.database_service.query(PendingPermission).filter(PendingPermission.id == pending_permission.id)
    )

  def delete_by_invite_id(self, invite_id):
    return self.services.database_service.delete(
      self.services.database_service.query(PendingPermission).filter(PendingPermission.invite_id == invite_id)
    )

  def delete_by_invite_ids(self, invite_ids):
    if invite_ids:
      return self.services.database_service.delete(
        self.services.database_service.query(PendingPermission).filter(PendingPermission.invite_id.in_(invite_ids))
      )
    return None

  def delete_by_client_ids(self, client_ids):
    return self.services.database_service.delete(
      self.services.database_service.query(PendingPermission).filter(PendingPermission.client_id.in_(client_ids))
    )

  def delete_by_email_and_client(self, email, client):
    invite = self.services.invite_service.find_by_email_and_organization(email, client.organization_id)
    if not invite:
      return None
    return self.services.database_service.delete(
      self.services.database_service.query(PendingPermission)
      .filter(PendingPermission.invite_id == invite.id)
      .filter(PendingPermission.client_id == client.id),
    )

  def delete_by_email_and_organization(self, email, organization):
    invite = self.services.invite_service.find_by_email_and_organization(email, organization.id)
    if not invite:
      return None
    return self.services.database_service.delete(
      self.services.database_service.query(PendingPermission).filter(PendingPermission.invite_id == invite.id)
    )

  def delete_by_email(self, email):
    invites = self.services.invite_service.find_by_email(email, valid_only=False)
    if not invites:
      return None
    return self.services.database_service.delete(
      self.services.database_service.query(PendingPermission).filter(
        PendingPermission.invite_id.in_([invite.id for invite in invites])
      )
    )
