# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime
from typing import Optional

from zigopt.common import *
from zigopt.common.sigopt_datetime import datetime_to_seconds
from zigopt.json.builder.json_builder import JsonBuilder, ValidationType, field
from zigopt.organization.model import Organization


class OrganizationJsonBuilder(JsonBuilder):
  object_name = "organization"

  def __init__(
    self,
    organization: Organization,
    last_activity: Optional[datetime.datetime] = None,
    optimized_runs_in_billing_cycle: Optional[int] = None,
    data_storage_bytes: Optional[int] = None,
    total_runs_in_billing_cycle: Optional[int] = None,
  ):
    self._organization = organization
    self._last_activity = last_activity
    self._optimized_runs_in_billing_cycle = optimized_runs_in_billing_cycle
    self._data_storage_bytes = data_storage_bytes
    self._total_runs_in_billing_cycle = total_runs_in_billing_cycle

  @field(ValidationType.id)
  def id(self) -> int:
    return self._organization.id

  @field(ValidationType.string)
  def name(self) -> str:
    return self._organization.name

  @field(ValidationType.integer)
  def created(self) -> Optional[float]:
    return napply(self._organization.date_created, datetime_to_seconds)

  def hide_deleted(self):
    return not self.deleted()

  @field(ValidationType.boolean, hide=hide_deleted)
  def deleted(self) -> bool:
    return self._organization.deleted

  @field(ValidationType.boolean)
  def academic(self) -> bool:
    return self._organization.academic

  def hide_last_activity(self):
    return not self._last_activity

  # only used by admins (for now)
  @field(ValidationType.integer, hide=hide_last_activity)
  def last_activity(self) -> Optional[float]:
    return napply(self._last_activity, datetime_to_seconds)

  @field(ValidationType.arrayOf(ValidationType.string))
  def email_domains(self) -> list[str]:
    return self._organization.organization_meta.email_domains

  @field(ValidationType.id)
  def client_for_email_signup(self) -> Optional[int]:
    return self._organization.organization_meta.GetFieldOrNone("client_for_email_signup")

  @field(ValidationType.boolean)
  def allow_signup_from_email_domains(self) -> bool:
    return self._organization.organization_meta.allow_signup_from_email_domains

  @field(ValidationType.integer)
  def optimized_runs_in_billing_cycle(self) -> Optional[int]:
    return self._optimized_runs_in_billing_cycle

  @field(ValidationType.integer)
  def data_storage_bytes(self) -> Optional[int]:
    return self._data_storage_bytes

  @field(ValidationType.integer)
  def total_runs_in_billing_cycle(self) -> Optional[int]:
    return self._total_runs_in_billing_cycle
