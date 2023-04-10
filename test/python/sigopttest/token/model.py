# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.common.strings import is_likely_random_string
from zigopt.token.model import Token
from zigopt.token.token_types import *


class TestToken:
  def test_default_token_object(self):
    token = Token(token_type=TokenType.CLIENT_API)
    assert is_likely_random_string(token.token)
    assert token.token_type == TokenType.CLIENT_API
    assert token.client_id is None
    assert token.user_id is None
    assert token.all_experiments is True
    assert token.guest_experiment_id is None
    assert token.creating_user_id is None
    assert token.guest_can_read is False
    assert token.guest_can_write is False
    assert token.development is False

  def test_token_expiry(self):
    now = unix_timestamp()
    token = Token(user_id="1", token_type=TokenType.GUEST)
    assert token.meta.date_created >= now
    assert token.expiration_timestamp is not None
    assert token.expired is False

  def test_token_expired(self):
    token = Token(user_id="1", token_type=TokenType.GUEST)
    token.meta.date_created = 1
    assert token.expiration_timestamp is not None
    assert token.expired is True

  def test_token_lasts_forever(self):
    now = unix_timestamp()
    token = Token(user_id="1", token_type=TokenType.GUEST)
    token.meta.lasts_forever = True
    assert token.meta.date_created >= now
    assert token.expiration_timestamp is None
    assert token.expired is False

  def test_user_token(self):
    token = Token(user_id="3", token_type=TokenType.USER)
    assert token.token_type == TokenType.USER
    assert token.development is False
    assert token.client_id is None
    assert token.user_id == "3"
    assert token.is_client_token is False
    assert token.is_user_token is True

  def test_client_token(self):
    token = Token(client_id="3", token_type=TokenType.CLIENT_API)
    assert token.token_type == TokenType.CLIENT_API
    assert token.development is False
    assert token.client_id == "3"
    assert token.user_id is None
    assert token.is_client_token is True
    assert token.is_user_token is False

  def test_development_token(self):
    token = Token(client_id="3", user_id="4", token_type=TokenType.CLIENT_DEV)
    assert token.token_type == TokenType.CLIENT_DEV
    assert token.development is True
    assert token.client_id == "3"
    assert token.user_id == "4"
    assert token.is_client_token is True
    assert token.is_user_token is False
    assert is_likely_random_string(token.token)
