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


class SessionJsonBuilder(JsonBuilder):
  object_name = "session"

  def __init__(self, session: Session):
    self._session = session

  @field(JsonBuilderValidationType())
  def api_token(self) -> Optional[str]:
    return napply(self._session.api_token, lambda tok: TokenJsonBuilder(tok, self._session.client))  # type: ignore

  @field(JsonBuilderValidationType())
  def client(self) -> Optional[ClientJsonBuilder]:
    return napply(self._session.client, ClientJsonBuilder)  # type: ignore

  @field(ValidationType.string)
  def code(self) -> str:
    return self._session.code

  @field(ValidationType.boolean)
  def needs_password_reset(self) -> bool:
    return bool(napply(self._session.user, lambda u: u.needs_password_reset))  # type: ignore

  @field(JsonBuilderValidationType())
  def user(self) -> Optional[UserJsonBuilder]:
    return napply(self._session.user, UserJsonBuilder)
