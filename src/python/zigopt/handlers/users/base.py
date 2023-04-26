# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.base.handler import Handler
from zigopt.net.errors import NotFoundError


class UserHandler(Handler):
  def __init__(self, services, request, user_id):
    if user_id is None:
      raise Exception("User id required")

    self.user_id = user_id
    self.user = None
    super().__init__(services, request)

  def find_objects(self):
    return extend_dict(
      super().find_objects(),
      {
        "user": self._find_user(self.user_id),
      },
    )

  def _find_user(self, user_id):
    if user_id:
      user = self.services.user_service.find_by_id(
        user_id,
        include_deleted=False,
      )
      if user:
        return user
    raise NotFoundError(f"No user {user_id}")

  def can_act_on_objects(self, requested_permission, objects):
    assert self.auth is not None

    return super().can_act_on_objects(requested_permission, objects) and self.auth.can_act_on_user(
      self.services, requested_permission, objects["user"]
    )
