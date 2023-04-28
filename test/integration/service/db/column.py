# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os

import pytest
from google.protobuf.internal.containers import *

from zigopt.common import *
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.db.column import JsonPath, jsonb_set
from zigopt.experiment.model import Experiment
from zigopt.protobuf.dict import protobuf_to_dict
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.protobuf.lib import copy_protobuf
from zigopt.protobuf.proxy import Proxy

from integration.service.db.test_base import DatabaseServiceBase
from sigopttest.common.sigopt_datetime import switch_to_system_timezone, switch_to_utc


OPTIONAL_FIELDS = [
  "client_provided_data",  # string
  "development",  # bool
  "experiment_type",  # ExperimentType
  "force_hitandrun_sampling",  # bool
  "unused_int64_key_for_testing",  # int64
  "observation_budget",  # int32
  "num_solutions",  # int32
]

REPEATED_FIELDS = [
  "all_parameters_unsorted",
  "metrics",
]

MAP_FIELDS = [
  "importance_maps",
]

FIELDS_WITH_VALUES = [
  # Format is (field_name, json_name, sample_value, sample_json_value)
  # Existing keys with new values
  ("client_provided_data", "client_provided_data", '{"abc":"def"}', '{"abc":"def"}'),
  ("observation_budget", "observation_budget", 120, 120),
  ("unused_int64_key_for_testing", "uuuuu", 121, "121"),  # NOTE: int64 is serialized as string
  ("development", "development", True, True),
  ("all_parameters_unsorted", "parameters", tuple([(ExperimentParameter(name="abc"))]), [{"name": "abc"}]),
  (
    "importance_maps",
    "imaps",
    {"metric1": (MetricImportanceMap(importances={"abc": MetricImportance(importance=2.0)}))},
    {"metric1": {"imps": {"abc": {"i": 2.0}}}},
  ),
  # New keys
  ("observation_budget", "observation_budget", 9, 9),
  ("force_hitandrun_sampling", "force_hitandrun_sampling", True, True),
  ("metrics", "metrics", tuple([(ExperimentMetric(name="abc"))]), [{"name": "abc"}]),
  ("num_solutions", "num_solutions", 5, 5),
]

INT_KEYS = [
  "observation_budget",  # int32,
  "unused_int64_key_for_testing",  # int64,
]


# pylint: disable=attribute-defined-outside-init
class TestProtobufColumn(DatabaseServiceBase):
  def empty_experiment(self, database_service):
    experiment = Experiment(
      client_id=1,
      name="empty experiment",
      experiment_meta=ExperimentMeta(),
    )
    database_service.insert(experiment)
    return experiment

  def full_experiment(self, database_service):
    experiment = Experiment(
      client_id=1,
      name="full experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[ExperimentParameter(name="param1", bounds=Bounds(minimum=4.0))],
        conditionals=[ExperimentConditional(name="cond1", values=[ExperimentConditionalValue(name="cv1")])],
        client_provided_data="{}",
        unused_int64_key_for_testing=13,
        observation_budget=60,
        development=False,
        importance_maps={"": MetricImportanceMap(importances={"param1": MetricImportance(importance=4.0)})},
      ),
    )
    database_service.insert(experiment)
    return experiment

  @pytest.fixture(params=["full", "empty"])
  def experiment(self, request, database_service):  # pylint: disable=arguments-renamed
    if request.param == "full":
      return self.full_experiment(database_service)
    return self.empty_experiment(database_service)

  @pytest.mark.parametrize("attr_name,json_name,sample_value,sample_json_value", FIELDS_WITH_VALUES)
  def test_jsonb_update(
    self,
    database_service,
    experiment_service,
    attr_name,
    json_name,
    sample_value,
    sample_json_value,
    experiment,
  ):
    orig_value = getattr(experiment.experiment_meta, attr_name)
    orig_json_value = protobuf_to_dict(experiment.experiment_meta).get(json_name)
    assert_neq(orig_value, sample_value)
    assert_neq(orig_json_value, sample_json_value)
    experiment_service.update_meta(experiment.id, {getattr(Experiment.experiment_meta, attr_name): sample_value})
    experiment = experiment_service.find_by_id(experiment.id)
    assert_eq(getattr(experiment.experiment_meta, attr_name), sample_value)
    assert_eq(protobuf_to_dict(experiment.experiment_meta).get(json_name), sample_json_value)

  @pytest.mark.parametrize("attr_name,json_name,sample_value,sample_json_value", FIELDS_WITH_VALUES)
  def test_jsonb_update_as_json_key(
    self,
    database_service,
    experiment_service,
    attr_name,
    json_name,
    sample_value,
    sample_json_value,
    experiment,
  ):
    orig_value = getattr(experiment.experiment_meta, attr_name)
    orig_json_value = protobuf_to_dict(experiment.experiment_meta).get(json_name)
    assert_neq(orig_value, sample_value)
    assert_neq(orig_json_value, sample_json_value)
    experiment_service.update_meta(experiment.id, {Experiment.experiment_meta[json_name]: sample_json_value})
    experiment = experiment_service.find_by_id(experiment.id)
    assert_eq(getattr(experiment.experiment_meta, attr_name), sample_value)
    assert_eq(protobuf_to_dict(experiment.experiment_meta).get(json_name), sample_json_value)

  def test_long_value_roundtrip(self, database_service, experiment_service, experiment):
    value_too_big_for_float = 2**62 + 1
    assert int(float(value_too_big_for_float)) != value_too_big_for_float
    assert experiment.experiment_meta.unused_int64_key_for_testing != value_too_big_for_float
    experiment_service.update_meta(
      experiment.id,
      {
        Experiment.experiment_meta.unused_int64_key_for_testing: value_too_big_for_float,
      },
    )
    experiment = experiment_service.find_by_id(experiment.id)
    assert experiment.experiment_meta.unused_int64_key_for_testing == value_too_big_for_float

  def test_long_value_comparison(self, database_service, experiment_service, experiment):
    # Since int64s are stored as strings, ensure that they are compared as ints
    smaller_value = 100
    value = 999
    larger_value = 1000
    assert smaller_value < value < larger_value
    assert str(value) > str(larger_value)
    assert str(value) > str(smaller_value)
    database_service.update(
      database_service.query(Experiment).filter(Experiment.id == experiment.id),
      {
        Experiment.experiment_meta: jsonb_set(
          Experiment.experiment_meta,
          JsonPath("uuuuu"),
          str(value),
        )
      },
    )
    assert (
      database_service.first(
        database_service.query(Experiment)
        .filter(Experiment.id == experiment.id)
        .filter(Experiment.experiment_meta.unused_int64_key_for_testing < larger_value)
      ).experiment_meta.unused_int64_key_for_testing
      == value
    )
    assert (
      database_service.first(
        database_service.query(Experiment)
        .filter(Experiment.id == experiment.id)
        .filter(Experiment.experiment_meta.unused_int64_key_for_testing < smaller_value)
      )
      is None
    )

  @pytest.mark.parametrize("key", INT_KEYS)
  @pytest.mark.parametrize("value", [123, "123"])
  def test_parse_int_format(self, database_service, experiment_service, key, value, experiment):
    database_service.update(
      database_service.query(Experiment).filter(Experiment.id == experiment.id),
      {Experiment.experiment_meta: jsonb_set(Experiment.experiment_meta, JsonPath(key), value)},
    )
    assert getattr(experiment_service.find_by_id(experiment.id).experiment_meta, key) == int(value)

  @pytest.mark.parametrize("key", OPTIONAL_FIELDS)
  def test_jsonb_set_null(self, database_service, experiment_service, key, experiment):
    experiment_service.update_meta(experiment.id, {getattr(Experiment.experiment_meta, key): None})
    experiment = experiment_service.find_by_id(experiment.id)
    assert not experiment.experiment_meta.HasField(key)

  @pytest.mark.parametrize("key", REPEATED_FIELDS)
  def test_jsonb_set_empty(self, database_service, experiment_service, key, experiment):
    experiment_service.update_meta(experiment.id, {getattr(Experiment.experiment_meta, key): []})
    experiment = experiment_service.find_by_id(experiment.id)
    assert len(getattr(experiment.experiment_meta, key)) == 0

  @pytest.mark.parametrize("key", MAP_FIELDS)
  def test_jsonb_map_fields(self, database_service, experiment_service, key, experiment):
    experiment_service.update_meta(experiment.id, {getattr(Experiment.experiment_meta, key): {}})
    experiment = experiment_service.find_by_id(experiment.id)
    assert len(getattr(experiment.experiment_meta, key)) == 0

  @pytest.mark.parametrize("key", OPTIONAL_FIELDS + REPEATED_FIELDS)
  def test_jsonb_set_identity(self, database_service, experiment_service, key, experiment):
    experiment_service.update_meta(
      experiment.id, {getattr(Experiment.experiment_meta, key): getattr(Experiment.experiment_meta, key)}
    )
    new_experiment = experiment_service.find_by_id(experiment.id)
    assert copy_protobuf(experiment.experiment_meta) == (copy_protobuf(new_experiment.experiment_meta))

  def test_jsonb_increment(self, database_service, experiment_service, experiment):
    old_budget = experiment_service.find_by_id(experiment.id).experiment_meta.observation_budget
    experiment_service.update_meta(
      experiment.id,
      {Experiment.experiment_meta.observation_budget: Experiment.experiment_meta.observation_budget + 1},
    )
    experiment = experiment_service.find_by_id(experiment.id)
    assert experiment.observation_budget == old_budget + 1

  def _compare_protobuf_values_to_db_values(self, experiment, database_service, select, cast):
    expected_value = select((experiment.experiment_meta))
    cast = cast or identity
    clause = cast(select(Experiment.experiment_meta))
    ((obj_id, value),) = database_service.all(
      database_service.query(Experiment.id, clause).filter_by(id=experiment.id).filter(clause == expected_value)
    )
    assert obj_id == experiment.id
    if isinstance(value, Proxy):
      value = value.underlying
      assert isinstance(expected_value, Proxy)
      expected_value = expected_value.underlying
    assert_eq(value, expected_value)
    assert database_service.all(database_service.query(clause == expected_value).filter_by(id=experiment.id)) == [
      (True,)
    ]

  @pytest.mark.parametrize(
    "i,select,cast",
    [
      (i, select, cast)
      for (i, (select, cast)) in enumerate(
        [
          (lambda meta: meta, None),
          (lambda meta: meta.experiment_type, lambda c: c.as_primitive()),
          (lambda meta: meta.HasField("experiment_type"), None),
          (lambda meta: meta.development, lambda c: c.as_primitive()),
          (lambda meta: meta.development, lambda c: ~~c),
          (lambda meta: meta.HasField("development"), None),
          (lambda meta: meta.force_hitandrun_sampling, lambda c: c.as_primitive()),
          (lambda meta: meta.force_hitandrun_sampling, lambda c: ~~c),
          (lambda meta: meta.HasField("force_hitandrun_sampling"), None),
          (lambda meta: meta.num_solutions, lambda c: c.as_primitive()),
          (lambda meta: meta.HasField("num_solutions"), None),
          (lambda meta: meta.metrics, None),
          (lambda meta: meta.importance_maps, None),
          (lambda meta: meta.importance_maps[""], None),
          (lambda meta: meta.importance_maps[""].importances, None),
          (lambda meta: meta.importance_maps[""].importances["param1"], None),
          (lambda meta: meta.importance_maps[""].importances["param1"].importance, lambda c: c.as_primitive()),
          (lambda meta: meta.all_parameters_unsorted, None),
          (lambda meta: meta.conditionals, None),
          (lambda meta: meta.observation_budget, lambda c: c.as_primitive()),
          (lambda meta: meta.unused_int64_key_for_testing, lambda c: c.as_primitive()),
          (lambda meta: meta.observation_budget, lambda c: c.as_primitive()),
          (lambda meta: meta.HasField("observation_budget"), None),
        ]
      )
    ],
  )
  def test_jsonb_field_access(self, i, database_service, experiment_service, select, cast):
    self._compare_protobuf_values_to_db_values(self.full_experiment(database_service), database_service, select, cast)
    self._compare_protobuf_values_to_db_values(self.empty_experiment(database_service), database_service, select, cast)

  @pytest.mark.parametrize(
    "i,select,cast",
    [
      (i, select, cast)
      for (i, (select, cast)) in enumerate(
        [
          (lambda meta: meta.all_parameters_unsorted[0], None),
          (lambda meta: meta.all_parameters_unsorted[0].name, lambda c: c.as_primitive()),
          (lambda meta: meta.all_parameters_unsorted[0].bounds, None),
          (lambda meta: meta.all_parameters_unsorted[0].bounds.minimum, lambda c: c.as_primitive()),
          (lambda meta: meta.all_parameters_unsorted[0].bounds.HasField("minimum"), None),
          (lambda meta: meta.all_parameters_unsorted[0].bounds.maximum, lambda c: c.as_primitive()),
          (lambda meta: meta.all_parameters_unsorted[0].bounds.HasField("maximum"), None),
          (lambda meta: meta.conditionals[0], None),
          (lambda meta: meta.conditionals[0].name, lambda c: c.as_primitive()),
          (lambda meta: meta.conditionals[0].HasField("name"), None),
          (lambda meta: meta.conditionals[0].values, None),
          (lambda meta: meta.conditionals[0].values[0], None),
          (lambda meta: meta.conditionals[0].values[0].name, lambda c: c.as_primitive()),
          (lambda meta: meta.conditionals[0].values[0].HasField("name"), None),
          (lambda meta: meta.conditionals[0].values[0].enum_index, lambda c: c.as_primitive()),
          (lambda meta: meta.conditionals[0].values[0].HasField("enum_index"), None),
        ]
      )
    ],
  )
  def test_jsonb_array_access(self, i, database_service, experiment_service, select, cast):
    self._compare_protobuf_values_to_db_values(self.full_experiment(database_service), database_service, select, cast)


class TestImpliedUTCDateTimeColumn(DatabaseServiceBase):
  @pytest.fixture(autouse=True)
  def reset_timezone(self):
    os.environ["TZ"] = "Etc/GMT+2"
    yield
    del os.environ["TZ"]
    switch_to_utc()

  @pytest.mark.parametrize("system_timezone", (True, False))
  def test_roundtrip(self, database_service, system_timezone):
    if system_timezone:
      switch_to_system_timezone()
    else:
      switch_to_utc()
    now = current_datetime()
    experiment = Experiment(client_id=1, name="empty experiment", date_created=now)
    database_service.insert(experiment)
    assert experiment.date_created == now
    assert (
      database_service.one(database_service.query(Experiment).filter(Experiment.id == experiment.id)).date_created
      == experiment.date_created
    )


def _normalize(value, expected_value):
  if is_sequence(value):
    assert is_sequence(expected_value)
    value = list(value)
    expected_value = list(expected_value)
  return value, expected_value


def assert_eq(value, expected_value):
  value, expected_value = _normalize(value, expected_value)
  assert value == expected_value


def assert_neq(value, expected_value):
  value, expected_value = _normalize(value, expected_value)
  assert value != expected_value
