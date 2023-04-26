# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.protobuf.gen.user.usermeta_pb2 import Usage
from zigopt.user.model import User


class PlannedUsageJsonBuilder(JsonBuilder):
  object_name = "planned_usage"

  def __init__(self, planned_usage: Usage):
    self._planned_usage = planned_usage

  @field(ValidationType.boolean)
  def track(self) -> Optional[bool]:
    if self._planned_usage.HasField("track"):
      return self._planned_usage.track
    return None

  @field(ValidationType.boolean)
  def optimize(self) -> Optional[bool]:
    if self._planned_usage.HasField("optimize"):
      return self._planned_usage.optimize
    return None


class UserJsonBuilder(JsonBuilder):
  object_name = "user"

  def __init__(self, user: User):
    self._user = user

  @field(ValidationType.integer)
  def created(self) -> Optional[int]:
    return self._user.date_created

  @field(ValidationType.boolean)
  def deleted(self) -> bool:
    return self._user.deleted

  @field(ValidationType.boolean, hide=lambda self: not self._user.is_educational_user)
  def educational_user(self) -> bool:
    return self._user.is_educational_user

  @field(ValidationType.string)
  def email(self) -> str:
    return self._user.email

  @field(ValidationType.boolean)
  def has_verified_email(self) -> bool:
    return self._user.has_verified_email

  @field(ValidationType.id)
  def id(self) -> int:
    return self._user.id

  @field(ValidationType.string)
  def name(self) -> str:
    return self._user.name

  @field(ValidationType.boolean)
  def show_welcome(self) -> bool:
    return self._user.user_meta.show_welcome

  @field(JsonBuilderValidationType())
  def planned_usage(self) -> PlannedUsageJsonBuilder:
    return PlannedUsageJsonBuilder(self._user.user_meta.planned_usage)
