# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from sqlalchemy.sql import text

from zigopt.common import *
from zigopt.client.model import Client
from zigopt.pagination.lib import PROTOBUF_FIELD_TYPE_TO_FIELD_API_TYPE, DefinedField, FieldApiType
from zigopt.training_run.field_types import TRAINING_RUN_API_FIELDS, FieldType
from zigopt.training_run.model import TrainingRun


class TrainingRunDefinedFieldsExtractor:
  def __init__(self, services, query, fields_details=None):
    self.services = services
    fields_details = coalesce(fields_details, TRAINING_RUN_API_FIELDS)
    self.id_query = self.services.database_service.query(aliased(TrainingRun, query.subquery()).id)
    self.fields_details = fields_details
    assert isinstance(self.fields_details, list)
    self.api_name_to_field_details = {field.api_name: field for field in self.fields_details}

  @generator_to_list
  def _count_primitive_fields(self, by_organization):
    names = []
    selectables = []
    for field in self.fields_details:
      if field.type in (FieldType.primitive, FieldType.protobuf_primitive):
        names.append((field.api_name,))
        selectables.append(field.sql_accessor)
      if field.type == FieldType.protobuf_object:
        for json_name in field.all_json_keys:
          names.append((field.api_name, json_name))
          selectables.append(field.sql_accessor[json_name])

    if selectables and not by_organization:
      counts = self.services.database_service.one_or_none(
        self.services.database_service.query(*[func.count(s) for s in selectables])
        .filter(TrainingRun.id.in_(self.id_query))
        .group_by(TrainingRun.client_id)
      )
    if selectables and by_organization:
      counts = self.services.database_service.one_or_none(
        self.services.database_service.query(*[func.count(s) for s in selectables])
        .join(Client, TrainingRun.client_id == Client.id)
        .filter(TrainingRun.id.in_(self.id_query))
        .group_by(Client.organization_id)
      )
    if selectables:
      counts = coalesce(counts, [0] * len(names))
      assert len(counts) == len(names)
      for (name, count) in zip(names, counts):
        yield name, count

  @generator_to_list
  def _get_user_defined_field_counts(self, api_name, field_type, json_name):
    # NOTE: Use Postgres lateral joins to get the information we want.
    # Hard to get sqlalchemy to do this right, so just unroll the SQL.
    # This means we need to manually compile and insert the WHERE clause from the provided query
    if field_type == FieldType.protobuf_map_of_object:
      tertiary_key = text("jsonb_object_keys(t2.value) AS tertiary")
    else:
      assert field_type == FieldType.protobuf_struct
      tertiary_key = text("NULL::text AS tertiary")
    subquery = (
      select([TrainingRun.id.label("id"), text("t2.key AS secondary"), tertiary_key])
      .select_from(text("jsonb_each(data -> :json_name) t2").bindparams(json_name=json_name))
      .where(TrainingRun.id.in_(self.id_query))
    )
    for result in self.services.database_service.execute(
      select([text("secondary"), text("tertiary"), func.count(text("id"))])
      .select_from(subquery.alias("x"))
      .group_by(text("secondary, tertiary"))
    ):
      yield (api_name, result[0], result[1]), result[2]

  @generator_to_list
  def _count_user_defined_fields(self):
    # TODO(SN-1127): Unwind this for loop, should be possible to UNION these queries together
    for field in self.fields_details:
      if field.type in (FieldType.protobuf_map_of_object, FieldType.protobuf_struct):
        yield from self._get_user_defined_field_counts(
          api_name=field.api_name,
          field_type=field.type,
          json_name=field.json_name,
        )

  @generator_to_list
  def _extract_count(self, by_organization):
    yield from self._count_primitive_fields(by_organization=by_organization)
    yield from self._count_user_defined_fields()

  @generator_to_list
  def extract_info(self, by_organization=False):
    for field_keys, count in self._extract_count(by_organization=by_organization):
      field_keys = [list_get(field_keys, 0), list_get(field_keys, 1), list_get(field_keys, 2)]
      api_type = FieldApiType.unknown
      name = None

      field_details = self.api_name_to_field_details[field_keys[0]]
      sortable = field_details.sortable
      if field_details.type == FieldType.protobuf_object:
        subfield = field_details.get_enclosed_sub_field_by_json_name(field_keys[1])
        if not subfield:
          continue
        api_type = PROTOBUF_FIELD_TYPE_TO_FIELD_API_TYPE.get(subfield.type, FieldApiType.unknown)
        field_keys = (field_keys[0], subfield.name, None)
      elif field_details.type is FieldType.protobuf_map_of_object:
        subfield = field_details.get_enclosed_sub_field_by_json_name(field_keys[2])
        if not subfield:
          continue
        api_type = PROTOBUF_FIELD_TYPE_TO_FIELD_API_TYPE.get(subfield.type, FieldApiType.unknown)
        field_keys = (field_keys[0], field_keys[1], subfield.name)
      elif field_details.type == FieldType.protobuf_struct:
        api_type = FieldApiType.unknown
        name = field_keys[-1]
      else:
        api_type = field_details.api_type
        name = field_details.readable_name

      key = ".".join(remove_nones(field_keys))
      yield DefinedField(
        api_type=api_type,
        field_count=count,
        key=key,
        name=name or key,
        sortable=sortable,
      )
