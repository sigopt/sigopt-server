# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import no_authentication, password_reset_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.users.sessions import BaseSessionHandler
from zigopt.handlers.validate.base import validate_email
from zigopt.handlers.validate.user import validate_user_password
from zigopt.json.builder import SessionJsonBuilder
from zigopt.net.errors import ForbiddenError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import NONE
from zigopt.protobuf.lib import copy_protobuf
from zigopt.user.model import User, password_hash, password_matches


class UsersChangePasswordHandler(BaseSessionHandler):
  authenticator = password_reset_authentication
  required_permissions = NONE

  Params = ImmutableStruct("Params", tuple(["new_plaintext_password"]))

  def parse_params(self, request):
    new_plaintext_password = validate_user_password(request.required_param("new_password"))
    return self.Params(new_plaintext_password=new_plaintext_password)

  def handle(self, params):
    assert self.auth is not None

    new_user_token = self.update_password(
      user_to_update=self.auth.current_user,
      new_plaintext_password=params.new_plaintext_password,
    )
    client = None
    if self.auth.authenticated_from_email_link:
      client = self.verify_email(self.auth.current_user)
    return SessionJsonBuilder.json(
      self.user_session(
        new_user_token,
        user=self.auth.current_user,
        client=client,
      )
    )

  def update_password(self, user_to_update, new_plaintext_password):
    # NOTE: If the user has no password, we should forbid it from being reset through this flow
    # However, we cannot perform this check until after the user has authed, to avoid leaking information
    # about an account.
    # There's no error worth returning though, since it should not be possible for the user to authenticate
    # with this endpoint if they have no password
    assert user_to_update.hashed_password

    if password_matches(new_plaintext_password, user_to_update.hashed_password):
      raise ForbiddenError("Cannot reuse your current password")

    new_meta = copy_protobuf(user_to_update.user_meta)
    new_meta.ClearField("hashed_password_reset_code")
    new_meta.ClearField("needs_password_reset")
    user_to_update.user_meta = new_meta

    self.services.database_service.update_one(
      self.services.database_service.query(User).filter(User.id == user_to_update.id),
      {
        User.hashed_password: password_hash(
          new_plaintext_password,
          work_factor=self.services.config_broker.get("user.password_work_factor"),
        ),
        User.user_meta: new_meta,
      },
    )

    self.services.email_router.send(
      self.services.email_templates.user_password_change_email(
        user_to_update,
      )
    )

    user_token = self.services.token_service.rotate_tokens_for_user(user_to_update.id)
    return user_token or self.services.token_service.create_temporary_user_token(user_to_update.id)


class UsersResetPasswordHandler(Handler):
  authenticator = no_authentication
  required_permissions = NONE

  def parse_params(self, request):
    return validate_email(request.required_param("email"))

  def handle(self, email):
    user = self.services.user_service.find_by_email(email)
    if user:
      if user.hashed_password:
        code = self.services.user_service.set_password_reset_code(user)
        self.services.email_router.send(
          self.services.email_templates.reset_password_email(
            user,
            code,
          )
        )
      else:
        self.services.email_router.send(self.services.email_templates.no_password_cant_reset_password_email(user))
    else:
      self.services.email_router.send(self.services.email_templates.no_user_cant_reset_password_email(email))
    return {}
