# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.json.builder import UserJsonBuilder

from sigopttest.json.builder.test_base import HIDDEN_USER_FIELDS, VISIBLE_USER_FIELDS, BuilderTestBase


def check_user_visible_fields(user, user_json):
  assert set(user_json.keys()) >= set(VISIBLE_USER_FIELDS) | {"object"}
  assert user_json["object"] == "user"
  assert user_json["created"] == user.date_created
  assert user_json["email"] == user.email
  assert user_json["has_verified_email"] == user.has_verified_email
  assert user_json["id"] == str(user.id)
  assert user_json["name"] == user.name
  assert user_json["planned_usage"]["track"] is None
  assert user_json["planned_usage"]["optimize"] is None
  assert user_json["show_welcome"] == user.show_welcome


class TestUserJsonBuilder(BuilderTestBase):
  def test_visible_fields(self, user):
    user_json = UserJsonBuilder.json(user)
    check_user_visible_fields(user, user_json)
    for hidden_field_name in HIDDEN_USER_FIELDS:
      assert hidden_field_name not in user_json

  def test_all_fields(self, user):
    user_meta = user.user_meta.copy_protobuf()
    user_meta.deleted = True
    user.user_meta = user_meta
    user_json = UserJsonBuilder.json(user)
    check_user_visible_fields(user, user_json)
    for hidden_field_name in HIDDEN_USER_FIELDS:
      assert hidden_field_name not in user_json
    assert user_json["deleted"] is True

  def test_educational_user(self, user):
    user_meta = user.user_meta.copy_protobuf()
    user_meta.educational_user = True
    user.user_meta = user_meta
    user_json = UserJsonBuilder.json(user)
    assert user_json["educational_user"] is True

  def test_no_extra_fields(self, user):
    user_json = UserJsonBuilder.json(user)
    assert set(user_json.keys()) == set(VISIBLE_USER_FIELDS) | {"object"}
