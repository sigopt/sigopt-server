# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.common import *
from zigopt.json.builder.client import ClientJsonBuilder
from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.json.builder.token import TokenJsonBuilder
from zigopt.json.builder.user import UserJsonBuilder
from zigopt.json.session import Session
from zigopt.token.model import Token
from zigopt.user.model import User


class SessionJsonBuilder(JsonBuilder):
  object_name = "session"

  def __init__(self, session: Session):
    self._session = session

  @field(JsonBuilderValidationType())
  def api_token(self) -> Optional[TokenJsonBuilder]:
    api_token: Optional[Token] = self._session_api_token
    return napply(api_token, lambda tok: TokenJsonBuilder(tok, self._session.client))

  @field(JsonBuilderValidationType())
  def client(self) -> Optional[ClientJsonBuilder]:
    return napply(self._session.client, ClientJsonBuilder)

  @field(ValidationType.string)
  def code(self) -> str:
    return self._session.code

  @field(ValidationType.boolean)
  def needs_password_reset(self) -> bool:
    user: Optional[User] = self._session.user
    return bool(napply(user, lambda u: u.needs_password_reset))

  @field(JsonBuilderValidationType())
  def user(self) -> Optional[UserJsonBuilder]:
    return napply(self._session.user, UserJsonBuilder)
