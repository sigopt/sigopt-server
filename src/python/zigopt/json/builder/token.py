# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.common import *
from zigopt.client.model import Client  # type: ignore
from zigopt.json.builder.json_builder import JsonBuilder, ValidationType, field
from zigopt.token.model import Token  # type: ignore
from zigopt.token.token_types import TOKEN_SCOPE_TO_NAME, PermissionType  # type: ignore


class TokenJsonBuilder(JsonBuilder):
  object_name = "token"

  def __init__(self, token: Token, client: Optional[Client] = None):
    if token.is_client_token:
      assert client is not None
      assert client.id == token.client_id
    self._token = token
    self._client = client

  @field(ValidationType.boolean)
  def all_experiments(self) -> bool:
    return self._token.all_experiments

  @field(ValidationType.id)
  def client(self) -> Optional[int]:
    return self._token.client_id

  @field(ValidationType.boolean)
  def development(self) -> bool:
    return self._token.development

  @field(ValidationType.id)
  def experiment(self) -> Optional[int]:
    return self._token.guest_experiment_id

  @field(ValidationType.id)
  def training_run(self) -> Optional[int]:
    return self._token.guest_training_run_id

  @field(ValidationType.id)
  def organization(self) -> Optional[int]:
    return self._client and self._client.organization_id

  @field(ValidationType.string)
  def permissions(self) -> str:
    if self._token.guest_can_read and not self._token.guest_can_write:
      return PermissionType.READ
    return PermissionType.WRITE

  @field(ValidationType.string)
  def scope(self) -> Optional[str]:
    return TOKEN_SCOPE_TO_NAME.get(self._token.scope)

  @field(ValidationType.string)
  def token(self) -> str:
    return self._token.token

  @field(ValidationType.string)
  def token_type(self) -> Optional[str]:
    return getattr(self._token, "token_type", None)

  @field(ValidationType.id)
  def user(self) -> Optional[int]:
    return self._token.user_id

  @field(ValidationType.integer)
  def expires(self) -> Optional[int]:
    return self._token.expiration_timestamp

  @field(ValidationType.integer)
  def lease_length(self) -> Optional[int]:
    return self._token.ttl_seconds
