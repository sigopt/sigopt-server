# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.common.strings import random_string
from zigopt.services.base import Service
from zigopt.user.model import password_hash


class EmailVerificationService(Service):
  @property
  def enabled(self):
    return self.services.config_broker.get("email.verify", True)

  def has_verified_email(self, user):
    return user.user_meta.has_verified_email

  def has_verified_email_if_needed(self, user):
    if self.enabled:
      return user.user_meta.has_verified_email
    return True

  def set_email_verification_code_without_save(self, user):
    meta = user.user_meta.copy_protobuf()
    email_verification_code = random_string()
    meta.hashed_email_verification_code = password_hash(email_verification_code)
    meta.email_verification_timestamp = unix_timestamp()
    meta.has_verified_email = False
    user.user_meta = meta
    return email_verification_code

  def declare_email_verified(self, user):
    user_meta = user.user_meta.copy_protobuf()
    update_user_meta = False
    if not user_meta.has_verified_email:
      self.services.email_router.send(self.services.email_templates.welcome_email(user))
      user_meta.has_verified_email = True
      update_user_meta = True

    for field in (
      "hashed_email_verification_code",
      "pending_client_name",
      "pending_client_id",
    ):
      if user_meta.HasField(field):
        user_meta.ClearField(field)
        update_user_meta = True

    if update_user_meta:
      self.services.user_service.update_meta(user, user_meta)
    user.user_meta = user_meta

  def send_verification_email(self, user, email_verification_code):
    self.services.email_router.send(
      self.services.email_templates.verification_email(
        user,
        email_verification_code,
      )
    )
