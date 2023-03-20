# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.json.builder import OwnerPermissionJsonBuilder, PermissionJsonBuilder

from sigopttest.json.builder.client import check_client_visible_fields
from sigopttest.json.builder.test_base import BuilderTestBase
from sigopttest.json.builder.user import check_user_visible_fields


class PermissionJsonBuilderTestBase(BuilderTestBase):
  @classmethod
  def check_permission_field_names(cls, permission_json):
    assert set(
      [
        "can_admin",
        "can_read",
        "can_see_experiments_by_others",
        "can_write",
        "client",
        "user",
        "is_owner",
        "object",
      ]
    ) == set(permission_json.keys())

  @classmethod
  def check_client_field(cls, client, permission_json):
    assert isinstance(permission_json["client"], dict)
    check_client_visible_fields(client, permission_json["client"])

  @classmethod
  def check_user_field(cls, user, permission_json):
    assert isinstance(permission_json["user"], dict)
    check_user_visible_fields(user, permission_json["user"])


class TestPermissionJsonBuilder(PermissionJsonBuilderTestBase):
  @classmethod
  def check_permission_fields(cls, permission, permission_json):
    cls.check_permission_field_names(permission_json)
    assert permission_json["can_admin"] is bool(permission.can_admin)
    assert permission_json["can_read"] is bool(permission.can_read)
    assert permission_json["can_see_experiments_by_others"] is bool(permission.can_see_experiments_by_others)
    assert permission_json["can_write"] is bool(permission.can_write)
    assert permission_json["is_owner"] is False
    assert permission_json["object"] == "permission"

  @classmethod
  def check_all_json_fields(cls, permission, client, user, permission_json):
    cls.check_permission_fields(permission, permission_json)
    cls.check_client_field(client, permission_json)
    cls.check_user_field(user, permission_json)

  def test_read_permission_fields(self, read_permission, client, user):
    permission_json = PermissionJsonBuilder.json(read_permission, client, user)
    self.check_all_json_fields(read_permission, client, user, permission_json)

  def test_write_permission_fields(self, write_permission, client, user):
    permission_json = PermissionJsonBuilder.json(write_permission, client, user)
    self.check_all_json_fields(write_permission, client, user, permission_json)

  def test_admin_permission_fields(self, admin_permission, client, user):
    permission_json = PermissionJsonBuilder.json(admin_permission, client, user)
    self.check_all_json_fields(admin_permission, client, user, permission_json)

  def test_null_user_field(self, admin_permission, client):
    permission_json = PermissionJsonBuilder.json(admin_permission, client, None)
    self.check_permission_field_names(permission_json)
    self.check_permission_fields(admin_permission, permission_json)
    self.check_client_field(client, permission_json)
    assert permission_json["user"] is None

  def test_null_client_field(self, admin_permission, user):
    permission_json = PermissionJsonBuilder.json(admin_permission, None, user)
    self.check_permission_field_names(permission_json)
    self.check_permission_fields(admin_permission, permission_json)
    assert permission_json["client"] is None
    self.check_user_field(user, permission_json)


class TestOwnerPermissionJsonBuilder(PermissionJsonBuilderTestBase):
  @classmethod
  def check_permission_fields(cls, permission_json):
    assert permission_json["can_admin"] is True
    assert permission_json["can_read"] is True
    assert permission_json["can_see_experiments_by_others"] is True
    assert permission_json["can_write"] is True
    assert permission_json["is_owner"] is True
    assert permission_json["object"] == "permission"

  @classmethod
  def check_all_json_fields(cls, client, user, permission_json):
    cls.check_permission_field_names(permission_json)
    cls.check_permission_fields(permission_json)
    cls.check_client_field(client, permission_json)
    cls.check_user_field(user, permission_json)

  def test_permission_fields(self, membership, client, user):
    permission_json = OwnerPermissionJsonBuilder.json(membership, client, user)
    self.check_all_json_fields(client, user, permission_json)

  def test_null_user_field(self, membership, client):
    permission_json = OwnerPermissionJsonBuilder.json(membership, client, None)
    self.check_permission_field_names(permission_json)
    self.check_permission_fields(permission_json)
    self.check_client_field(client, permission_json)
    assert permission_json["user"] is None

  def test_null_client_field(self, membership, user):
    permission_json = OwnerPermissionJsonBuilder.json(membership, None, user)
    self.check_permission_field_names(permission_json)
    self.check_permission_fields(permission_json)
    assert permission_json["client"] is None
    self.check_user_field(user, permission_json)
