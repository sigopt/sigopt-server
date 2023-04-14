# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy.exc import IntegrityError

from zigopt.client.model import Client
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.common.strings import random_string
from zigopt.membership.model import Membership, MembershipType
from zigopt.services.base import Service
from zigopt.user.model import User, normalize_email, password_hash

from libsigopt.aux.errors import SigoptValidationError


class UserService(Service):
  def find_by_id(self, user_id, include_deleted=False):
    return self.services.database_service.one_or_none(
      self._include_deleted_clause(
        include_deleted,
        self.services.database_service.query(User).filter_by(id=user_id),
      )
    )

  def find_by_ids(self, user_ids, include_deleted=False):
    if user_ids:
      return self.services.database_service.all(
        self._include_deleted_clause(
          include_deleted, self.services.database_service.query(User).filter(User.id.in_(user_ids))
        )
      )
    return []

  def find_by_email(self, email, include_deleted=False):
    return self.services.database_service.one_or_none(
      self._include_deleted_clause(
        include_deleted,
        self.services.database_service.query(User).filter(User.email == normalize_email(email)),
      )
    )

  def _include_deleted_clause(self, include_deleted, q):
    if not include_deleted:
      return q.filter(~User.user_meta.deleted.as_boolean())
    return q

  def insert(self, user):
    return self.services.database_service.insert(user)

  def create_new_user(self, user):
    try:
      self.insert(user)
    except IntegrityError as e:
      self.services.database_service.rollback_session()
      preexisting_user = self.find_by_email(user.email, include_deleted=True)
      if not preexisting_user.deleted:
        self.services.email_router.send(self.services.email_templates.existing_email(user))
        raise SigoptValidationError("Please verify email.") from e
      random_code = random_string(str_length=8)
      new_email = f"deleted-{random_code}-{preexisting_user.email}"
      preexisting_user.email = new_email
      self.services.database_service.upsert(preexisting_user)
      self.insert(user)
    self.services.database_service.flush_session()

  def set_password_reset_code(self, user):
    code = random_string()
    meta = user.user_meta.copy_protobuf()
    meta.hashed_password_reset_code = password_hash(code, self.services.config_broker.get("user.password_work_factor"))
    meta.password_reset_timestamp = unix_timestamp()
    self.services.user_service.update_meta(user, meta)
    return code

  def change_user_email_without_save(self, user, new_email):
    existing_user = self.services.user_service.find_by_email(new_email)
    if existing_user is not None:
      raise SigoptValidationError("Unable to change email.")

    email_verification_code = self.services.email_verification_service.set_email_verification_code_without_save(user)
    user_meta = user.user_meta.copy_protobuf()
    user_meta.ClearField("public_cert")
    user.email = new_email
    return email_verification_code

  def delete(self, user):
    meta = user.user_meta.copy_protobuf()
    meta.deleted = True
    meta.date_deleted = unix_timestamp()
    self.update_meta(user, meta)

  def update_meta(self, user, meta):
    user.user_meta = meta
    return self.services.database_service.update_one(
      self.services.database_service.query(User).filter(User.id == user.id),
      {User.user_meta: meta},
    )

  def find_owned_clients(self, user):
    return self.services.database_service.all(
      self.services.database_service.query(Client)
      .join(Membership, Membership.organization_id == Client.organization_id)
      .filter(Membership.membership_type == MembershipType.owner)
      .filter(Membership.user_id == user.id)
    )
