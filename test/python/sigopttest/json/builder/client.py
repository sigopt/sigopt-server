# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.json.builder import ClientJsonBuilder
from zigopt.protobuf.lib import copy_protobuf

from sigopttest.json.builder.test_base import HIDDEN_CLIENT_FIELDS, VISIBLE_CLIENT_FIELDS, BuilderTestBase


def check_client_visible_fields(client, client_json):
  assert set(client_json.keys()) >= set(VISIBLE_CLIENT_FIELDS) | {"object"}
  assert client_json["id"] == str(client.id)
  assert client_json["organization"] == str(client.organization_id)
  assert client_json["name"] == client.name
  assert client_json["created"] == client.date_created
  client_security_json = client_json["client_security"]
  assert isinstance(client_security_json, dict)
  autsebo = "allow_users_to_see_experiments_by_others"
  assert autsebo in client_security_json
  assert client_security_json[autsebo] == getattr(client, autsebo)


class TestClientJsonBuilder(BuilderTestBase):
  def test_visible_fields(self, client):
    client_json = ClientJsonBuilder.json(client)
    check_client_visible_fields(client, client_json)
    for hidden_field_name in HIDDEN_CLIENT_FIELDS:
      assert hidden_field_name not in client_json

  def test_all_fields(self, client):
    client_meta = copy_protobuf(client.client_meta)
    client_meta.deleted = True
    client.client_meta = client_meta
    client_json = ClientJsonBuilder.json(client)
    check_client_visible_fields(client, client_json)
    for hidden_field_name in HIDDEN_CLIENT_FIELDS:
      assert hidden_field_name in client_json
    assert client_json["deleted"] is True

  def test_no_extra_fields(self, client):
    client_json = ClientJsonBuilder.json(client)
    assert set(client_json.keys()) ^ set(VISIBLE_CLIENT_FIELDS) == {"object"}
