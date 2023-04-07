# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.common import *
from zigopt.client.model import Client
from zigopt.json.builder.client import ClientJsonBuilder
from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.json.builder.user import UserJsonBuilder
from zigopt.membership.model import Membership
from zigopt.permission.model import Permission
from zigopt.user.model import User


class BasePermissionJsonBuilder(JsonBuilder):
  object_name = "permission"

  def __init__(self, client: Client, user: User):
    self._client = client
    self._user = user

  @field(ValidationType.boolean)
  def can_admin(self) -> bool:
    raise NotImplementedError()

  @field(ValidationType.boolean)
  def can_read(self) -> bool:
    raise NotImplementedError()

  @field(ValidationType.boolean)
  def can_see_experiments_by_others(self) -> bool:
    raise NotImplementedError()

  @field(ValidationType.boolean)
  def can_write(self) -> bool:
    raise NotImplementedError()

  @field(JsonBuilderValidationType())
  def client(self) -> Optional[ClientJsonBuilder]:
    return napply(self._client, ClientJsonBuilder)

  @field(ValidationType.boolean)
  def is_owner(self) -> bool:
    raise NotImplementedError()

  @field(JsonBuilderValidationType())
  def user(self) -> Optional[UserJsonBuilder]:
    return napply(self._user, UserJsonBuilder)


class PermissionJsonBuilder(BasePermissionJsonBuilder):
  def __init__(self, permission: Permission, client: Client, user: User):
    super().__init__(client, user)
    self._permission = permission
    self._client = client
    self._user = user

  @field(ValidationType.boolean)
  def can_admin(self) -> bool:
    return bool(self._permission.can_admin)

  @field(ValidationType.boolean)
  def can_read(self) -> bool:
    return bool(self._permission.can_read)

  @field(ValidationType.boolean)
  def can_see_experiments_by_others(self) -> bool:
    return bool(self._permission.can_see_experiments_by_others)

  @field(ValidationType.boolean)
  def can_write(self) -> bool:
    return bool(self._permission.can_write)

  @field(ValidationType.boolean)
  def is_owner(self) -> bool:
    return False


class OwnerPermissionJsonBuilder(BasePermissionJsonBuilder):
  def __init__(self, membership: Membership, client: Client, user: User):
    assert membership.is_owner
    super().__init__(client, user)
    self._client = client
    self._user = user

  @field(ValidationType.boolean)
  def can_admin(self) -> bool:
    return True

  @field(ValidationType.boolean)
  def can_read(self) -> bool:
    return True

  @field(ValidationType.boolean)
  def can_see_experiments_by_others(self) -> bool:
    return True

  @field(ValidationType.boolean)
  def can_write(self) -> bool:
    return True

  @field(ValidationType.boolean)
  def is_owner(self) -> bool:
    return True
