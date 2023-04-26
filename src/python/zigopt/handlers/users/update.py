# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.users.base import UserHandler
from zigopt.handlers.validate.user import validate_user_email, validate_user_name, validate_user_password
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.json.builder import UserJsonBuilder
from zigopt.net.errors import ForbiddenError, NotFoundError
from zigopt.protobuf.lib import copy_protobuf
from zigopt.user.model import do_password_hash_work_factor_update, password_matches

from libsigopt.aux.errors import MissingParamError, SigoptValidationError


class UsersUpdateHandler(UserHandler):
  authenticator = api_token_authentication
  NOT_PROVIDED = object()

  Params = ImmutableStruct(
    "Params",
    (
      "name",
      "educational_user",
      "email",
      "password",
      "show_welcome",
      "planned_usage",
    ),
  )

  def parse_params(self, request):
    data = request.params()
    name = get_opt_with_validation(data, "name", ValidationType.string)
    if name is not None:
      name = validate_user_name(name)
    educational_user = get_opt_with_validation(data, "educational_user", ValidationType.boolean)
    email = get_opt_with_validation(data, "email", ValidationType.string)
    # NOTE: password only used when email provided
    password = None
    if email is not None:
      email = validate_user_email(email)
      password = get_opt_with_validation(data, "password", ValidationType.string)
      if password is not None:
        password = validate_user_password(password)

    if "planned_usage" in data:
      planned_usage = get_opt_with_validation(data, "planned_usage", ValidationType.object)
    else:
      planned_usage = self.NOT_PROVIDED
    show_welcome = get_opt_with_validation(data, "show_welcome", ValidationType.boolean)
    return UsersUpdateHandler.Params(
      name=name,
      educational_user=educational_user,
      email=email,
      password=password,
      show_welcome=show_welcome,
      planned_usage=planned_usage,
    )

  def handle(self, uploaded_user):
    user_json = UserJsonBuilder.json(self.do_update(self.user.id, uploaded_user))
    self.services.iam_logging_service.log_iam(
      requestor=self.auth.current_user,
      event_name=IamEvent.USER_UPDATE,
      request_parameters=remove_nones(
        {
          "user_id": self.user.id,
          "name": uploaded_user.name,
          "educational_user": uploaded_user.educational_user,
          "email": uploaded_user.email,
          "show_welcome": uploaded_user.show_welcome,
          "planned_usage": None if uploaded_user.planned_usage is self.NOT_PROVIDED else uploaded_user.planned_usage,
        }
      ),
      response_element=user_json,
      response_status=IamResponseStatus.SUCCESS,
    )
    return user_json

  def do_update(self, user_id, uploaded_user):
    user = self.services.user_service.find_by_id(user_id)
    if not user:
      raise NotFoundError(f"No user with id {user_id}")

    if uploaded_user.name is not None:
      user.name = uploaded_user.name

    if uploaded_user.educational_user is not None:
      user_meta = copy_protobuf(user.user_meta)
      user_meta.educational_user = uploaded_user.educational_user
      user.user_meta = user_meta

    old_email = user.email
    new_email = uploaded_user.email
    if new_email is not None:
      if not user.hashed_password:
        raise SigoptValidationError("You cannot change your email because your account is externally administered.")
      if uploaded_user.password is None:
        raise MissingParamError("password")
      if not password_matches(uploaded_user.password, user.hashed_password):
        raise ForbiddenError("Invalid password")
      do_password_hash_work_factor_update(self.services, user, uploaded_user.password)

      email_verification_code = self.services.user_service.change_user_email_without_save(user, new_email)

    show_welcome = uploaded_user.show_welcome
    if show_welcome is not None:
      user_meta = copy_protobuf(user.user_meta)
      user_meta.show_welcome = show_welcome
      user.user_meta = user_meta

    planned_usage = uploaded_user.planned_usage
    if planned_usage is None:
      user.user_meta.ClearField("planned_usage")
    elif planned_usage is self.NOT_PROVIDED:
      pass
    else:
      user_meta = copy_protobuf(user.user_meta)
      user_meta.planned_usage.optimize = planned_usage.get("optimize", user_meta.planned_usage.optimize)
      user_meta.planned_usage.track = planned_usage.get("track", user_meta.planned_usage.track)
      user.user_meta = user_meta

    self.services.database_service.upsert(user)
    if new_email:
      self.services.email_router.send(
        self.services.email_templates.user_email_change_email(old_email=old_email, new_email=new_email)
      )
      self.services.email_verification_service.send_verification_email(user, email_verification_code)

    return user
