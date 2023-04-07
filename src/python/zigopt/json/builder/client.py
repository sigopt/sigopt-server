# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime
from typing import Optional

from zigopt.common import *
from zigopt.client.model import Client
from zigopt.common.sigopt_datetime import datetime_to_seconds
from zigopt.json.builder.json_builder import JsonBuilder, ValidationType, field


class ClientJsonBuilder(JsonBuilder):
  object_name = "client"

  def __init__(self, client: Client, last_activity: Optional[datetime.datetime] = None):
    self._client = client
    self._last_activity = last_activity

  @field(ValidationType.id)
  def id(self) -> int:
    return self._client.id

  @field(ValidationType.id)
  def organization(self) -> int:
    return self._client.organization_id

  @field(ValidationType.string)
  def name(self) -> str:
    return self._client.name

  @field(ValidationType.integer)
  def created(self) -> int:
    return self._client.date_created

  @field(ValidationType.object)
  def client_security(self) -> dict[str, bool]:
    return dict(
      allow_users_to_see_experiments_by_others=self._client.allow_users_to_see_experiments_by_others,
    )

  def hide_deleted(self):
    return not self.deleted()

  @field(ValidationType.boolean, hide=hide_deleted)
  def deleted(self) -> bool:
    return self._client.deleted

  def hide_last_activity(self):
    return not self._last_activity

  # only used by admins (for now)
  @field(ValidationType.integer, hide=hide_last_activity)
  def last_activity(
    self,
  ) -> Optional[float]:
    return napply(self._last_activity, datetime_to_seconds)
