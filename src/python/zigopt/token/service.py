# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Sequence

from zigopt.common import *
from zigopt.common.sigopt_datetime import unix_timestamp_seconds
from zigopt.db.column import JsonPath, jsonb_set, unwind_json_path
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ, TokenMeta
from zigopt.services.base import Service
from zigopt.token.model import MAX_CONCURRENT_SESSIONS, USER_TOKEN_EXPIRY_SECONDS, Token
from zigopt.token.token_types import TokenType


class TokenService(Service):
  def _reject_expired(self, tokens: Sequence[Token]):
    expired, valid = partition(remove_nones_sequence(tokens, list), lambda t: t.expired)
    if expired:
      self.delete_tokens(expired)
    return valid

  def find_by_token(self, token, include_expired=False):
    token = self.services.database_service.one_or_none(
      self.services.database_service.query(Token).filter(Token.token == token)
    )
    if include_expired or self._reject_expired([token]):
      return token
    return None

  def find_guest_tokens(self, client_id, creating_user_id):
    assert client_id is not None
    query = (
      self.services.database_service.query(Token)
      .filter(Token.client_id == client_id)
      .filter(Token.token_type == TokenType.GUEST)
    )

    if creating_user_id is not None:
      query = query.filter(Token.meta.creating_user_id.as_integer() == creating_user_id)

    return self._reject_expired(self.services.database_service.all(query))

  def find_by_user_id(self, user_id, token_type=None):
    q = self.services.database_service.query(Token).filter(Token.user_id == user_id)
    if token_type is not None:
      q = q.filter(Token.token_type == token_type)
    return self._reject_expired(self.services.database_service.all(q))

  def find_by_client_and_user(self, client_id, user_id):
    return self._reject_expired(
      self.services.database_service.all(
        self.services.database_service.query(Token)
        .filter(Token.client_id == client_id)
        .filter(Token.user_id == user_id)
      )
    )

  def _make_meta(self, session_expiration: int | None, token_type, can_renew):
    now = unix_timestamp_seconds()
    meta = TokenMeta()
    meta.date_created = now
    meta.can_renew = can_renew
    ttl_options: Sequence[int | None] = [
      Token.default_ttl_seconds(token_type, can_renew),
      napply(session_expiration, lambda s: max(s - now, 0)),
      self.services.config_broker.get("external_authorization.token_ttl_seconds"),
    ]
    meta.SetFieldIfNotNone(  # type: ignore
      "ttl_seconds",
      min_option(remove_nones_sequence(ttl_options, list)),
    )
    return meta

  def _get_or_create_role_token(self, client_id, user_id, development):
    assert client_id is not None
    assert user_id is not None
    existing = [token for token in self.find_by_client_and_user(client_id, user_id) if token.development == development]
    if existing:
      return existing[0]
    token_type = TokenType.CLIENT_DEV if development else TokenType.CLIENT_API
    meta = self._make_meta(session_expiration=None, token_type=token_type, can_renew=False)
    meta.creating_user_id = user_id
    new = Token(token_type=token_type, user_id=user_id, client_id=client_id, meta=meta)
    self.services.database_service.insert(new)
    return new

  def get_or_create_role_token(self, client_id, user_id):
    return self._get_or_create_role_token(client_id, user_id, development=False)

  def get_or_create_development_role_token(self, client_id, user_id):
    return self._get_or_create_role_token(client_id, user_id, development=True)

  def _is_guest_read_token(self, token, creating_user_id=None):
    return (
      token.token_type == TokenType.GUEST
      and token.user_id is None
      and (creating_user_id is None or token.creating_user_id == creating_user_id)
      and token.guest_experiment_id is None
      and token.guest_can_read
      and not token.expired
      and token.scope == TokenMeta.SIGNUP_SCOPE
    )

  def get_client_signup_token(self, client_id, creating_user_id=None):
    assert client_id is not None
    return find(
      self.find_guest_tokens(client_id=client_id, creating_user_id=creating_user_id),
      self._is_guest_read_token,
    )

  def get_or_create_client_signup_token(self, client_id, creating_user_id):
    assert client_id is not None
    assert creating_user_id is not None
    token_type = TokenType.GUEST
    existing = self.get_client_signup_token(client_id, creating_user_id=creating_user_id)
    if existing:
      return existing
    meta = self._make_meta(session_expiration=None, token_type=token_type, can_renew=False)
    meta.creating_user_id = creating_user_id
    meta.guest_permissions = READ
    meta.lasts_forever = True
    meta.scope = TokenMeta.SIGNUP_SCOPE
    new = Token(token_type=token_type, client_id=client_id, meta=meta)
    assert self._is_guest_read_token(new)
    self.services.database_service.insert(new)
    return new

  def _make_guest_token_meta(self, session_expiration, creating_user_id):
    token_type = TokenType.GUEST
    meta = self._make_meta(session_expiration=session_expiration, token_type=token_type, can_renew=False)
    meta.guest_permissions = READ
    meta.scope = TokenMeta.SHARED_EXPERIMENT_SCOPE
    if creating_user_id:
      meta.creating_user_id = creating_user_id
    return meta

  def create_guest_experiment_token(self, client_id, experiment_id, creating_user_id, session_expiration):
    meta = self._make_guest_token_meta(session_expiration=session_expiration, creating_user_id=creating_user_id)
    meta.guest_experiment_id = experiment_id
    new = Token(token_type=TokenType.GUEST, client_id=client_id, user_id=None, meta=meta)
    self.services.database_service.insert(new)
    return new

  def create_guest_training_run_token(
    self,
    client_id,
    training_run_id,
    experiment_id,
    creating_user_id,
    session_expiration,
  ):
    meta = self._make_guest_token_meta(session_expiration=session_expiration, creating_user_id=creating_user_id)
    meta.guest_training_run_id = training_run_id
    meta.SetFieldIfNotNone("guest_experiment_id", experiment_id)
    new = Token(token_type=TokenType.GUEST, client_id=client_id, user_id=None, meta=meta)
    self.services.database_service.insert(new)
    return new

  def create_temporary_user_token(self, user_id, session_expiration=None):
    if not session_expiration:
      ttl_seconds = self.services.config_broker.get("login_session.idle_timeout_seconds", USER_TOKEN_EXPIRY_SECONDS)
      session_expiration = unix_timestamp_seconds() + ttl_seconds
    return self._create_user_token(user_id, session_expiration, can_renew=False)

  def _create_user_token(self, user_id, session_expiration, can_renew):
    token_type = TokenType.USER
    max_concurrent_sessions = self.services.config_broker.get(
      "login_session.max_concurrent_sessions",
      MAX_CONCURRENT_SESSIONS,
    )
    current_user_tokens = self.find_by_user_id(user_id, token_type=token_type)
    if len(current_user_tokens) >= max_concurrent_sessions:
      oldest_token = min(current_user_tokens, key=lambda t: t.meta.date_created)
      self.delete_token(oldest_token)
    meta = self._make_meta(session_expiration, token_type=token_type, can_renew=can_renew)
    new = Token(token_type=token_type, client_id=None, user_id=user_id, meta=meta)
    self.services.database_service.insert(new)
    return new

  def renew_token(self, token):
    now = unix_timestamp_seconds()
    updated = self.services.database_service.update_one_or_none(
      self.services.database_service.query(Token)
      .filter(Token.token == token.token)
      .filter(Token.meta.can_renew.as_boolean()),
      {Token.meta: jsonb_set(Token.meta, JsonPath(*unwind_json_path(Token.meta.date_renewed)), now)},
    )
    if updated:
      meta = token.meta.copy_protobuf()
      meta.date_renewed = now
      token.meta = meta
      return token
    return None

  def rotate_token(self, token):
    token_string = random_string()

    updated = self.services.database_service.update_one_or_none(
      self.services.database_service.query(Token).filter(Token.token == token.token), {Token.token: token_string}
    )

    if updated:
      token.token = token_string
      return token
    return None

  def update_meta(self, token, meta):
    self.services.database_service.update_one(
      self.services.database_service.query(Token).filter(Token.token == token.token),
      {Token.meta: meta},
    )
    token.meta = meta
    return token

  def rotate_tokens_for_user(self, user_id):
    user_token = None
    for token in self.find_by_user_id(user_id):
      rotated_token = self.services.token_service.rotate_token(token)
      if rotated_token and rotated_token.token_type == TokenType.USER:
        user_token = rotated_token
    return user_token

  def delete_token(self, token):
    deleted = self.services.database_service.delete_one_or_none(
      self.services.database_service.query(Token).filter(Token.token == token.token)
    )
    return deleted

  def delete_tokens(self, tokens):
    deleted = self.services.database_service.delete(
      self.services.database_service.query(Token).filter(Token.token.in_([t.token for t in tokens]))
    )
    return deleted
