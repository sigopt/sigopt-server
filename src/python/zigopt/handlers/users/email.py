# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import no_authentication, user_token_authentication
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.users.base import UserHandler
from zigopt.protobuf.gen.token.tokenmeta_pb2 import NONE


class BaseResendVerificationEmailHandler(Handler):
  def send_verification_email_to_user(self, user):
    token = self.services.email_verification_service.set_email_verification_code_without_save(user)
    self.services.user_service.update_meta(user, user.user_meta)
    self.services.email_verification_service.send_verification_email(user, token)


class UsersResendVerificationEmailHandler(BaseResendVerificationEmailHandler, UserHandler):
  authenticator = user_token_authentication

  def handle(self):
    self.send_verification_email_to_user(self.user)
    return {}


class ResendVerificationEmailHandler(BaseResendVerificationEmailHandler, Handler):
  authenticator = no_authentication
  required_permissions = NONE

  def parse_params(self, request):
    return request.required_param("email")

  def handle(self, email):
    user = self.services.user_service.find_by_email(email)
    if user and not self.services.email_verification_service.has_verified_email(user):
      self.send_verification_email_to_user(user)
    return {}
