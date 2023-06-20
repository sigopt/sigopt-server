# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import time
from http import HTTPStatus

import pytest

from zigopt.db.column import JsonPath, jsonb_set, unwind_json_path
from zigopt.token.model import Token

from integration.base import RaisesApiException
from integration.connection import IntegrationTestConnection
from integration.v1.test_base import V1Base


class TestTokenUpdate(V1Base):
  def test_rotate(self, connection, config_broker, api):
    token_value = connection.conn.user_token
    user_id = connection.sessions().fetch().user
    new_token = connection.tokens("self").update(token="rotate").token
    assert new_token != token_value
    # Second call to rotate should fail, because the previous token should no longer be valid
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.tokens("self").update(token="rotate")
    new_conn = IntegrationTestConnection(api_url=connection.api_url, user_token=new_token)
    assert new_conn.sessions().fetch().user == user_id
    new_conn.tokens("self").update(token="rotate")

  def test_lasts_forever(self, connection, config_broker):
    e = connection.create_any_experiment()
    token_value = connection.experiments(e.id).tokens().create().token
    response_token = connection.tokens(token_value).update(lasts_forever=True)
    assert response_token.token == token_value
    assert response_token.expires is None
    response_token = connection.tokens(token_value).update(lasts_forever=False)
    assert response_token.token == token_value
    assert response_token.expires is not None

  def test_lasts_forever_as_non_admin(self, connection, config_broker, api):
    e = connection.create_any_experiment()
    token_value = connection.experiments(e.id).tokens().create().token
    response_token = connection.tokens(token_value).update(lasts_forever=True)
    assert response_token.expires is None
    assert response_token.token == token_value
    response_token = connection.tokens(token_value).update(lasts_forever=False)
    assert response_token.expires is not None
    assert response_token.token == token_value

  def test_renew_token(self, connection):
    initial_expires = connection.tokens("self").fetch().expires
    time.sleep(1)
    connection.tokens("self").update(expires="renew")
    assert connection.tokens("self").fetch().expires > initial_expires

  def test_cant_renew_expired(self, connection, db_connection):
    connection.tokens("self").update(expires="renew")
    assert db_connection.update(
      db_connection.query(Token).filter(Token.token == connection.user_token),
      {Token.meta: jsonb_set(Token.meta, JsonPath(*unwind_json_path(Token.meta.date_renewed)), 1)},
    )
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.tokens("self").update(expires="renew")

  def test_cant_renew_wrong_token_type(self, connection):
    e = connection.create_any_experiment()
    token_value = connection.experiments(e.id).tokens().create().token
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.tokens(token_value).update(expires="renew")

  def test_cant_update_fake_token(self, connection):
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.tokens("SOME_FAKE_TOKEN").update(token="rotate")
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.tokens("SOME_FAKE_TOKEN").update(lasts_forever=True)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.tokens("SOME_FAKE_TOKEN").update(expires="renew")

  @pytest.mark.parametrize(
    "update_kwargs",
    (
      dict(),
      dict(lasts_forever=True),
      dict(token="rotate"),
    ),
  )
  def test_cant_modify_as_guest(self, connection, config_broker, api, update_kwargs):
    e = connection.create_any_experiment()
    token_value = connection.experiments(e.id).tokens().create().token
    guest_conn = IntegrationTestConnection(api_url=connection.api_url, client_token=token_value)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      guest_conn.tokens("self").update(**update_kwargs)
