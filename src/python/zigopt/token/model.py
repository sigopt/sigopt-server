# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from datetime import timedelta

from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import validates

from zigopt.common import *
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.common.strings import random_string
from zigopt.db.column import ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ, WRITE, TokenMeta
from zigopt.token.token_types import ALL_TOKEN_TYPES, TokenType


GUEST_TOKEN_EXPIRY_SECONDS = int(timedelta(days=30).total_seconds())
USER_TOKEN_EXPIRY_SECONDS = int(timedelta(days=7).total_seconds())
TOKEN_TYPE_DB_ENUM = Enum(*ALL_TOKEN_TYPES, name="token_types")
MAX_CONCURRENT_SESSIONS = 20


class Token(Base):
  __tablename__ = "tokens"

  token = Column(String, primary_key=True)
  token_type = Column(TOKEN_TYPE_DB_ENUM)
  client_id = Column(BigInteger, ForeignKey("clients.id", name="tokens_client_id_fkey"), index=True)
  user_id = Column(BigInteger, ForeignKey("users.id", name="tokens_user_id_fkey", ondelete="CASCADE"), index=True)
  meta = ProtobufColumn(TokenMeta, name="token_meta_json")

  def __init__(self, *args, **kwargs):
    if not kwargs.get("meta"):
      kwargs["meta"] = TokenMeta(date_created=unix_timestamp())
    if not kwargs.get("token"):
      kwargs["token"] = random_string()
    super().__init__(*args, **kwargs)

  @validates("meta")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta)

  @property
  def all_experiments(self):
    if self.guest_can_write:
      return True
    if self.token_type in [TokenType.CLIENT_API, TokenType.CLIENT_DEV, TokenType.USER]:
      return True
    return False

  @property
  def guest_experiment_id(self):
    return (self.token_type == TokenType.GUEST and self.meta.guest_experiment_id) or None

  @property
  def guest_training_run_id(self):
    return (self.token_type == TokenType.GUEST and self.meta.guest_training_run_id) or None

  @staticmethod
  def default_ttl_seconds(token_type, can_renew):
    if token_type == TokenType.GUEST:
      return GUEST_TOKEN_EXPIRY_SECONDS
    if token_type == TokenType.USER:
      # TODO(SN-999): why is default for USER tokens to never expire? Seems wrong but
      # probably doesn't matter since all USER tokens are now temporary which explicitly set ttl_seconds
      # so we never need to check the default
      return USER_TOKEN_EXPIRY_SECONDS if can_renew else None
    return None

  @property
  def ttl_seconds(self) -> int | None:
    if self.is_userless_client_token:
      return None
    if self.meta.lasts_forever:
      return None
    return coalesce(
      self.meta.ttl_seconds,
      Token.default_ttl_seconds(self.token_type, can_renew=self.meta.can_renew),
    )

  @property
  def expiration_timestamp(self):
    start_date = coalesce(self.meta.date_renewed, self.meta.date_created)
    return napply(self.ttl_seconds, lambda t: start_date + t)

  @property
  def expired(self):
    now = unix_timestamp()
    if self.expiration_timestamp is not None:
      return now > self.expiration_timestamp
    return False

  @property
  def is_userless_client_token(self):
    return self.token_type == TokenType.GUEST and self.user_id is None and self.guest_experiment_id is None

  @property
  def is_client_token(self):
    return self.token_type in [TokenType.CLIENT_API, TokenType.CLIENT_DEV, TokenType.GUEST]

  @property
  def is_user_token(self):
    return self.token_type == TokenType.USER

  @property
  def creating_user_id(self):
    return self.meta.creating_user_id or None

  @property
  def _guest_permissions(self):
    return (self.token_type == TokenType.GUEST and self.meta.guest_permissions) or None

  @property
  def guest_can_read(self):
    return self._guest_permissions in {READ, WRITE}

  @property
  def guest_can_write(self):
    return self._guest_permissions == WRITE

  @property
  def development(self):
    return self.token_type == TokenType.CLIENT_DEV

  @property
  def scope(self):
    return self.meta.scope
