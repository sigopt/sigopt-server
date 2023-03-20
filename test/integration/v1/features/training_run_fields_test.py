# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random

import pytest

from zigopt.common.strings import random_string
from zigopt.protobuf.dict import dict_to_protobuf_struct
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import Log, TrainingRunData
from zigopt.training_run.field_types import *
from zigopt.training_run.model import TrainingRun

from integration.v1.test_base import V1Base


fields_details = [
  ProtobufPrimitiveFieldDetails(
    "name",
    TrainingRun.training_run_data,
    api_type=FieldApiType.string,
    protobuf_field_name="name",
  ),
  ProtobufPrimitiveFieldDetails(
    "state",
    TrainingRun.training_run_data,
    api_type=FieldApiType.string,
    protobuf_field_name="state",
  ),
  ProtobufStructFieldDetails(
    "metadata",
    TrainingRun.training_run_data,
    api_type=FieldApiType.unknown,
    protobuf_field_name="metadata",
  ),
  ProtobufMapFieldDetails(
    "logs",
    TrainingRun.training_run_data,
    api_type=FieldApiType.object,
    protobuf_field_name="logs",
  ),
]

rst = random_string
fields_test_information = dict(
  # field=(example_value, addendum to field to get expected key)
  created=(random.randint(0, 100), ""),
  observation=(random.randint(0, 100), ""),
  name=(rst(10), ""),
  state=(TrainingRunData.COMPLETED, ""),
  metadata=(dict_to_protobuf_struct(dict(user_provided_key=rst(10))), "user_provided_key"),
  logs=(
    dict(stdout=Log(content=rst(10))),
    "stdout.content",
  ),
)

example_values = {field: test_info[0] for field, test_info in fields_test_information.items()}
expected_keys = {
  field: ".".join([field, test_info[1]]) if test_info[1] != "" else field
  for field, test_info in fields_test_information.items()
}


class TestFieldsInfoExtractor(V1Base):
  @pytest.mark.parametrize("field_details", fields_details)
  def test_extract_info(self, field_details, connection):
    client_id = connection.client_id
    model_field = {field_details.api_name: example_values[field_details.api_name]}
    if field_details.type == FieldType.primitive:
      model_instance = TrainingRun(client_id=client_id, **model_field)
    else:
      model_instance = TrainingRun(client_id=client_id, training_run_data=TrainingRunData(**model_field))
    self.services.database_service.insert(model_instance)

    query = self.services.database_service.query(TrainingRun).filter(TrainingRun.client_id == client_id)
    fields_info = self.services.training_run_service.fetch_stored_fields(query, [field_details])
    assert len(fields_info) == 1
    (field_info,) = fields_info
    assert field_info.field_count == 1
    assert field_info.key == expected_keys.get(field_details.api_name)
