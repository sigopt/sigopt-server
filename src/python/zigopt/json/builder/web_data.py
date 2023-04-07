# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.common import *
from zigopt.common.sigopt_datetime import datetime_to_seconds
from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.web_data.lib import validate_web_data_dict
from zigopt.web_data.model import WebData


class ProjectResourceIdBuilder(JsonBuilder):
  object_name = "project_resource_id"

  def __init__(self, web_data: WebData):
    self._web_data = web_data

  @field(ValidationType.id_string)
  def project(self) -> str:
    return self._web_data.project_reference_id

  @field(ValidationType.id)
  def client(self) -> int:
    return self._web_data.project_client_id


parent_resource_id_builders_by_resource = {"project": ProjectResourceIdBuilder}
validate_web_data_dict(parent_resource_id_builders_by_resource, depth=1)


class WebDataJsonBuilder(JsonBuilder):
  object_name = "web_data"

  def __init__(self, web_data: WebData):
    self._web_data = web_data

  @field(ValidationType.id)
  def id(self) -> int:
    return self._web_data.id

  @field(ValidationType.id)
  def created_by(self) -> Optional[int]:
    return self._web_data.created_by

  @field(ValidationType.integer)
  def updated(self) -> Optional[float]:
    return napply(self._web_data.updated, datetime_to_seconds)

  @field(ValidationType.integer)
  def created(self) -> Optional[float]:
    return napply(self._web_data.created, datetime_to_seconds)

  @field(ValidationType.string)
  def display_name(self) -> Optional[str]:
    return self._web_data.display_name

  @field(ValidationType.string)
  def parent_resource_type(self) -> Optional[str]:
    return self._web_data.parent_resource_type

  @field(ValidationType.string)
  def web_data_type(self) -> Optional[str]:
    return self._web_data.web_data_type

  @field(JsonBuilderValidationType())
  def parent_resource_id(self) -> JsonBuilder:
    return parent_resource_id_builders_by_resource[self._web_data.parent_resource_type](self._web_data)

  @field(ValidationType.object)
  def payload(self) -> dict:
    return self._web_data.payload
