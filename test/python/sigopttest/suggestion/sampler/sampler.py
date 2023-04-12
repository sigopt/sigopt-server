# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random

import numpy
import pytest
from flaky import flaky
from mock import Mock
from scipy import stats

from zigopt.experiment.model import Experiment, ExperimentParameterProxy
from zigopt.experiment.segmenter import ExperimentParameterSegmenter
from zigopt.math.initialization import get_low_discrepancy_stencil_length_from_experiment
from zigopt.math.interval import ClosedInterval, LeftOpenInterval, OpenInterval, RightOpenInterval
from zigopt.observation.model import Observation
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  PARAMETER_CATEGORICAL,
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  ExperimentCategoricalValue,
  ExperimentConditional,
  ExperimentConditionalValue,
  ExperimentConstraint,
  ExperimentMeta,
  ExperimentParameter,
  ParameterCondition,
  Prior,
)
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData
from zigopt.sigoptcompute.adapter import SCAdapter
from zigopt.suggestion.sampler.categorical import CategoricalOnlySampler
from zigopt.suggestion.sampler.grid import GridSampler
from zigopt.suggestion.sampler.lhc import LatinHypercubeSampler
from zigopt.suggestion.sampler.random import RandomSampler
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from sigopttest.base.config_broker import StrictAccessConfigBroker
from sigopttest.base.utils import partial_opt_args


class TestSuggestSampler:
  # pylint: disable=too-many-public-methods
  @pytest.fixture
  def segmenter(self):
    return ExperimentParameterSegmenter(Mock())

  @pytest.fixture
  def services(self, segmenter):
    return self.mock_services(segmenter, [])

  def mock_services(self, segmenter, observations):
    return Mock(
      config_broker=StrictAccessConfigBroker.from_configs(
        {
          "optimize": {
            "rejection_sampling_trials": 10000,
          },
        }
      ),
      experiment_parameter_segmenter=segmenter,
      observation_service=Mock(all_data=Mock(return_value=observations)),
      sc_adapter=SCAdapter(Mock()),
    )

  def suggestion_to_observation(self, experiment, suggestion, id_num=None):
    observation_kwargs = {"data": ObservationData(assignments_map=suggestion.get_assignments(experiment))}
    if id_num is not None:
      observation_kwargs["id"] = id_num
    return Observation(**observation_kwargs)

  def assert_exclusively_in(self, value, intervals, interval_index):
    for i, interval in enumerate(intervals):
      if i == interval_index:
        assert value in interval
      else:
        assert value not in interval

  def int_parameter(self, minimum, maximum, grid=None, conditions=None, name=None):
    parameter = ExperimentParameter()
    if name is None:
      parameter.name = "i_" + str(random.randint(0, 99999999))
    else:
      parameter.name = name
    parameter.param_type = PARAMETER_INT
    parameter.bounds.minimum = minimum
    parameter.bounds.maximum = maximum
    if isinstance(grid, list):
      parameter.grid_values.extend(grid)
      parameter.ClearField("bounds")
    if conditions:
      parameter.conditions.extend(conditions)
    return ExperimentParameterProxy(parameter)

  def double_parameter(self, minimum, maximum, grid=None, conditions=None, has_prior=False, log_scale=False, name=None):
    parameter = ExperimentParameter()
    if name is None:
      parameter.name = "d_" + str(random.randint(0, 99999999))
    else:
      parameter.name = name
    parameter.param_type = PARAMETER_DOUBLE
    parameter.bounds.minimum = minimum
    parameter.bounds.maximum = maximum
    if isinstance(grid, list):
      parameter.grid_values.extend(grid)
      parameter.ClearField("bounds")
    if conditions:
      parameter.conditions.extend(conditions)
    if has_prior:
      parameter.prior.prior_type = Prior.BETA
      parameter.prior.beta_prior.shape_a = 2
      parameter.prior.beta_prior.shape_b = 3.5
    if log_scale:
      parameter.transformation = ExperimentParameter.TRANSFORMATION_LOG
    return ExperimentParameterProxy(parameter)

  def categorical_parameter(self, values, grid=None, conditions=None, name=None):
    parameter = ExperimentParameter()
    if name is None:
      parameter.name = "c_" + str(random.randint(0, 99999999))
    else:
      parameter.name = name
    parameter.param_type = PARAMETER_CATEGORICAL
    parameter.all_categorical_values.extend([v.copy_protobuf() for v in values])
    if isinstance(grid, list):
      parameter.grid_values.extend(grid)
    if conditions:
      parameter.conditions.extend(conditions)
    return ExperimentParameterProxy(parameter)

  def conditional_parameter(self, name, values, grid=None):
    conditional = ExperimentConditional()
    conditional.name = name
    conditional.values.extend(values)
    return conditional

  def test_coverage(self, segmenter):
    # pylint: disable=too-many-locals,too-many-statements
    int_parameter = self.int_parameter(0, 10)
    double_parameter = self.double_parameter(3, 5)
    categorical_parameter = self.categorical_parameter(
      [
        ExperimentCategoricalValue(enum_index=0),
        ExperimentCategoricalValue(enum_index=1),
        ExperimentCategoricalValue(enum_index=2),
      ]
    )
    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          int_parameter.copy_protobuf(),
          double_parameter.copy_protobuf(),
          categorical_parameter.copy_protobuf(),
        ],
      ),
    )

    observations = []
    services = self.mock_services(segmenter, observations)
    sampler = LatinHypercubeSampler(services, experiment, partial_opt_args())
    stencil_length = sampler.stencil_length

    multi_suggestions = sampler.fetch_best_suggestions(stencil_length)
    for suggestion in multi_suggestions:
      assert len(suggestion.get_assignments(experiment)) == 3
      assert suggestion.get_assignment(categorical_parameter) in [0, 1, 2]
      assert suggestion.get_assignment(int_parameter) in range(0, 11)
      assert suggestion.get_assignment(double_parameter) in ClosedInterval(3, 5)
    multi_observations = [self.suggestion_to_observation(experiment, s) for s in multi_suggestions]

    for _ in range(stencil_length):
      optimization_args = partial_opt_args(observation_count=len(observations), observation_iterator=observations)
      sampler = LatinHypercubeSampler(services, experiment, optimization_args)
      suggestion = sampler.fetch_best_suggestions(1)[0]
      observations.append(self.suggestion_to_observation(experiment, suggestion))

      assert len(suggestion.get_assignments(experiment)) == 3
      assert suggestion.get_assignment(categorical_parameter) in [0, 1, 2]
      assert suggestion.get_assignment(int_parameter) in range(0, 11)
      assert suggestion.get_assignment(double_parameter) in ClosedInterval(3, 5)

    for check in (observations, multi_observations):
      categorical_observations = [o.get_assignment(categorical_parameter) for o in check]
      assert len(categorical_observations) == stencil_length
      assert len([c == 0 for c in categorical_observations]) >= 1
      assert len([c == 1 for c in categorical_observations]) >= 1
      assert len([c == 2 for c in categorical_observations]) >= 1

      int_observations = [o.get_assignment(int_parameter) for o in check]
      assert len(int_observations) == stencil_length
      assert len([c in [0, 1, 2] for c in int_observations]) >= 1
      assert len([c in [3, 4, 5] for c in int_observations]) >= 1
      assert len([c in [5, 6, 7] for c in int_observations]) >= 1
      assert len([c in [8, 9, 10] for c in int_observations]) >= 1

      double_observations = [o.get_assignment(double_parameter) for o in check]
      assert len(double_observations) == stencil_length
      assert len([c in ClosedInterval(3, 3.5) for c in double_observations]) >= 1
      assert len([c in ClosedInterval(3.5, 4) for c in double_observations]) >= 1
      assert len([c in ClosedInterval(4, 4.5) for c in double_observations]) >= 1
      assert len([c in ClosedInterval(4.5, 5) for c in double_observations]) >= 1

    suggestions = []
    for _ in range(stencil_length):
      optimization_args = partial_opt_args(observation_count=0, open_suggestions=suggestions)
      sampler = LatinHypercubeSampler(services, experiment, optimization_args)
      suggestion = sampler.fetch_best_suggestions(1)[0]
      suggestions.append(suggestion)

      assert len(suggestion.get_assignments(experiment)) == 3
      assert suggestion.get_assignment(categorical_parameter) in [0, 1, 2]
      assert suggestion.get_assignment(int_parameter) in range(0, 11)
      assert suggestion.get_assignment(double_parameter) in ClosedInterval(3, 5)
    observations = [self.suggestion_to_observation(experiment, s) for s in suggestions]

    for check in (observations, multi_observations):
      categorical_observations = [o.get_assignment(categorical_parameter) for o in check]
      assert len(categorical_observations) == stencil_length
      assert len([c == 0 for c in categorical_observations]) >= 1
      assert len([c == 1 for c in categorical_observations]) >= 1
      assert len([c == 2 for c in categorical_observations]) >= 1

      int_observations = [o.get_assignment(int_parameter) for o in check]
      assert len(int_observations) == stencil_length
      assert len([c in [0, 1, 2] for c in int_observations]) >= 1
      assert len([c in [3, 4, 5] for c in int_observations]) >= 1
      assert len([c in [5, 6, 7] for c in int_observations]) >= 1
      assert len([c in [8, 9, 10] for c in int_observations]) >= 1

      double_observations = [o.get_assignment(double_parameter) for o in check]
      assert len(double_observations) == stencil_length
      assert len([c in ClosedInterval(3, 3.5) for c in double_observations]) >= 1
      assert len([c in ClosedInterval(3.5, 4) for c in double_observations]) >= 1
      assert len([c in ClosedInterval(4, 4.5) for c in double_observations]) >= 1
      assert len([c in ClosedInterval(4.5, 5) for c in double_observations]) >= 1

  def test_constrained_random_sampler(self, segmenter):
    # pylint: disable=too-many-locals
    int_parameter_1 = self.int_parameter(0, 10, name="i_1")
    int_parameter_2 = self.int_parameter(10, 20, name="i_2")
    double_parameter_1 = self.double_parameter(30, 40, name="d_1")
    double_parameter_2 = self.double_parameter(40, 50, name="d_2")
    categorical_parameter_1 = self.categorical_parameter(
      [
        ExperimentCategoricalValue(enum_index=0),
        ExperimentCategoricalValue(enum_index=1),
        ExperimentCategoricalValue(enum_index=2),
      ],
      name="c_1",
    )
    categorical_parameter_2 = self.categorical_parameter(
      [
        ExperimentCategoricalValue(enum_index=0),
        ExperimentCategoricalValue(enum_index=1),
        ExperimentCategoricalValue(enum_index=2),
      ],
      name="c_2",
    )
    constraints = [
      ExperimentConstraint(
        type="greater_than",
        rhs=80,
        terms=[
          dict(name=double_parameter_1.name, coeff=1),
          dict(name=double_parameter_2.name, coeff=1),
        ],
      ),
      ExperimentConstraint(
        type="less_than",
        rhs=85,
        terms=[
          dict(name=double_parameter_1.name, coeff=1),
          dict(name=double_parameter_2.name, coeff=1),
        ],
      ),
    ]
    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          int_parameter_1.copy_protobuf(),
          int_parameter_2.copy_protobuf(),
          double_parameter_1.copy_protobuf(),
          double_parameter_2.copy_protobuf(),
          categorical_parameter_1.copy_protobuf(),
          categorical_parameter_2.copy_protobuf(),
        ],
        constraints=constraints,
      ),
    )

    observations = []
    services = self.mock_services(segmenter, observations)
    sampler = RandomSampler(services, experiment, UnprocessedSuggestion.Source.EXPLICIT_RANDOM)
    stencil_length = 2 * len(experiment.experiment_meta.all_parameters_unsorted)
    suggestions = sampler.generate_random_suggestions(stencil_length)
    for suggestion in suggestions:
      assert len(suggestion.get_assignments(experiment)) == 6
      assert suggestion.get_assignment(categorical_parameter_1) in [0, 1, 2]
      assert suggestion.get_assignment(categorical_parameter_2) in [0, 1, 2]
      assert suggestion.get_assignment(int_parameter_1) in range(0, 11)
      assert suggestion.get_assignment(int_parameter_2) in range(10, 21)
      assert suggestion.get_assignment(double_parameter_1) in ClosedInterval(30, 40)
      assert suggestion.get_assignment(double_parameter_2) in ClosedInterval(40, 50)
      assert suggestion.get_assignment(double_parameter_1) + suggestion.get_assignment(double_parameter_2) >= 80
      assert suggestion.get_assignment(double_parameter_1) + suggestion.get_assignment(double_parameter_2) <= 85

  def test_integer_constrained_sampler(self, segmenter):
    # pylint: disable=too-many-locals
    c1 = 70
    c2 = 85
    c3 = 0.5
    int_parameter_1 = self.int_parameter(1, 50, name="a")
    int_parameter_2 = self.int_parameter(51, 100, name="g")
    double_parameter_1 = self.double_parameter(0, 1, name="b")
    double_parameter_2 = self.double_parameter(0, 1, name="f")
    categorical_parameter_1 = self.categorical_parameter(
      [
        ExperimentCategoricalValue(enum_index=0),
        ExperimentCategoricalValue(enum_index=1),
        ExperimentCategoricalValue(enum_index=2),
      ],
      name="c",
    )
    categorical_parameter_2 = self.categorical_parameter(
      [
        ExperimentCategoricalValue(enum_index=0),
        ExperimentCategoricalValue(enum_index=1),
        ExperimentCategoricalValue(enum_index=2),
      ],
      name="z",
    )
    constraints = [
      ExperimentConstraint(
        type="greater_than",
        rhs=c1,
        terms=[
          dict(name=int_parameter_1.name, coeff=1),
          dict(name=int_parameter_2.name, coeff=1),
        ],
      ),
      ExperimentConstraint(
        type="less_than",
        rhs=c2,
        terms=[
          dict(name=int_parameter_1.name, coeff=1),
          dict(name=int_parameter_2.name, coeff=1),
        ],
      ),
      ExperimentConstraint(
        type="less_than",
        rhs=c3,
        terms=[
          dict(name=double_parameter_1.name, coeff=1),
          dict(name=double_parameter_2.name, coeff=1),
        ],
      ),
    ]
    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          int_parameter_1.copy_protobuf(),
          int_parameter_2.copy_protobuf(),
          double_parameter_1.copy_protobuf(),
          double_parameter_2.copy_protobuf(),
          categorical_parameter_1.copy_protobuf(),
          categorical_parameter_2.copy_protobuf(),
        ],
        constraints=constraints,
      ),
    )

    observations = []
    services = self.mock_services(segmenter, observations)
    sampler = RandomSampler(services, experiment, UnprocessedSuggestion.Source.EXPLICIT_RANDOM)
    stencil_length = 2 * len(experiment.experiment_meta.all_parameters_unsorted)
    suggestions = sampler.generate_random_suggestions(stencil_length)
    for suggestion in suggestions:
      assert len(suggestion.get_assignments(experiment)) == 6
      assert suggestion.get_assignment(categorical_parameter_1) in [0, 1, 2]
      assert suggestion.get_assignment(categorical_parameter_2) in [0, 1, 2]
      assert suggestion.get_assignment(int_parameter_1) in range(1, 50)
      assert suggestion.get_assignment(int_parameter_2) in range(51, 100)
      assert suggestion.get_assignment(double_parameter_1) in ClosedInterval(0, 1)
      assert suggestion.get_assignment(double_parameter_2) in ClosedInterval(0, 1)
      assert suggestion.get_assignment(int_parameter_1) + suggestion.get_assignment(int_parameter_2) >= c1
      assert suggestion.get_assignment(int_parameter_1) + suggestion.get_assignment(int_parameter_2) <= c2
      assert suggestion.get_assignment(double_parameter_1) + suggestion.get_assignment(double_parameter_2) <= c3

  def test_latin_hypercube_double_parameter_log_transform(self, segmenter):
    parameter = self.double_parameter(1e-5, 1, log_scale=True)
    intervals = segmenter.segmented_intervals(parameter, 5)
    assert len(intervals) == 5

    self.assert_exclusively_in(random.uniform(1e-5, 1e-4), intervals, 0)
    self.assert_exclusively_in(random.uniform(1e-4, 1e-3), intervals, 1)
    self.assert_exclusively_in(random.uniform(1e-3, 1e-2), intervals, 2)
    self.assert_exclusively_in(random.uniform(1e-2, 1e-1), intervals, 3)
    self.assert_exclusively_in(random.uniform(1e-1, 1), intervals, 4)

  def test_latin_hypercube_int_parameter(self, segmenter):
    parameter = self.int_parameter(0, 10)
    intervals = segmenter.segmented_intervals(parameter, 5)
    assert len(intervals) == 5
    for interval in intervals:
      assert -1 not in interval
      assert 11 not in interval

    self.assert_exclusively_in(0, intervals, 0)
    self.assert_exclusively_in(1, intervals, 0)
    self.assert_exclusively_in(2, intervals, 1)
    self.assert_exclusively_in(3, intervals, 1)
    self.assert_exclusively_in(4, intervals, 2)
    self.assert_exclusively_in(6, intervals, 3)
    self.assert_exclusively_in(8, intervals, 4)
    self.assert_exclusively_in(9, intervals, 4)
    self.assert_exclusively_in(10, intervals, 4)

    intervals = segmenter.segmented_intervals(parameter, 3)
    assert len(intervals) == 3
    for interval in intervals:
      assert -1 not in interval
      assert 11 not in interval

    self.assert_exclusively_in(0, intervals, 0)
    self.assert_exclusively_in(1, intervals, 0)
    self.assert_exclusively_in(2, intervals, 0)
    self.assert_exclusively_in(3, intervals, 0)
    self.assert_exclusively_in(4, intervals, 1)
    self.assert_exclusively_in(5, intervals, 1)
    self.assert_exclusively_in(6, intervals, 1)
    self.assert_exclusively_in(7, intervals, 2)
    self.assert_exclusively_in(8, intervals, 2)
    self.assert_exclusively_in(9, intervals, 2)
    self.assert_exclusively_in(10, intervals, 2)

    intervals = segmenter.segmented_intervals(parameter, 17)
    assert len(intervals) == 17
    for interval in intervals:
      assert -1 not in interval
      assert 11 not in interval

    self.assert_exclusively_in(0, intervals, 0)
    self.assert_exclusively_in(1, intervals, 1)
    self.assert_exclusively_in(5, intervals, 8)
    self.assert_exclusively_in(9, intervals, 15)
    self.assert_exclusively_in(10, intervals, 16)

    intervals = segmenter.segmented_intervals(parameter, 1)
    assert len(intervals) == 1
    assert -1 not in intervals[0]
    assert 11 not in intervals[0]
    assert 0 in intervals[0]
    assert 10 in intervals[0]

  def test_latin_hypercube_categorical_parameter(self, segmenter):
    real_values = [
      ExperimentCategoricalValue(enum_index=0),
      ExperimentCategoricalValue(enum_index=1),
      ExperimentCategoricalValue(enum_index=2),
      ExperimentCategoricalValue(enum_index=3),
      ExperimentCategoricalValue(enum_index=4),
      ExperimentCategoricalValue(enum_index=5),
    ]
    deleted_value = ExperimentCategoricalValue(enum_index=100, deleted=True)

    def size(interval):
      return len([v for v in [v.enum_index for v in real_values] if v in interval])

    parameter = self.categorical_parameter(real_values + [deleted_value])

    intervals = segmenter.segmented_intervals(parameter, 3)
    assert len(intervals) == 3
    assert len([i for i in intervals if size(i) == 2]) == 3
    for interval in intervals:
      for i in interval:
        assert deleted_value.enum_index != i
    self.assert_exclusively_in(real_values[0].enum_index, intervals, 0)
    self.assert_exclusively_in(real_values[1].enum_index, intervals, 0)
    self.assert_exclusively_in(real_values[2].enum_index, intervals, 1)
    self.assert_exclusively_in(real_values[3].enum_index, intervals, 1)
    self.assert_exclusively_in(real_values[4].enum_index, intervals, 2)
    self.assert_exclusively_in(real_values[5].enum_index, intervals, 2)

    intervals = segmenter.segmented_intervals(parameter, 1)
    assert len(intervals) == 1
    assert len([i for i in intervals if size(i) == 6]) == 1
    for interval in intervals:
      for i in interval:
        assert deleted_value.enum_index != i
    self.assert_exclusively_in(real_values[0].enum_index, intervals, 0)
    self.assert_exclusively_in(real_values[1].enum_index, intervals, 0)
    self.assert_exclusively_in(real_values[2].enum_index, intervals, 0)
    self.assert_exclusively_in(real_values[3].enum_index, intervals, 0)
    self.assert_exclusively_in(real_values[4].enum_index, intervals, 0)
    self.assert_exclusively_in(real_values[5].enum_index, intervals, 0)

    intervals = segmenter.segmented_intervals(parameter, 10)
    assert len(intervals) == 10
    assert len([i for i in intervals if size(i) == 1]) == 6
    assert len([i for i in intervals if size(i) == 0]) == 4
    for interval in intervals:
      for i in interval:
        assert deleted_value.enum_index != i
    self.assert_exclusively_in(real_values[0].enum_index, intervals, 0)
    self.assert_exclusively_in(real_values[5].enum_index, intervals, 9)

  @pytest.mark.parametrize(
    "grid_values",
    [
      [0.1, 0.3, 0.5, 0.7, 0.9, 1.1],
      [0.1, 0.2, 0.4, 0.6, 1.0, 1.8],
    ],
  )
  @pytest.mark.parametrize("log_scale", [True, False])
  def test_latin_hypercube_grid_parameter_even_spacing(self, segmenter, grid_values, log_scale):
    def size(interval):
      return len([v for v in grid_values if v in interval])

    parameter = self.double_parameter(0, 1, grid_values, log_scale=log_scale)

    intervals = segmenter.segmented_intervals(parameter, 3)
    assert len(intervals) == 3
    assert len([i for i in intervals if size(i) == 2]) == 3
    self.assert_exclusively_in(grid_values[0], intervals, 0)
    self.assert_exclusively_in(grid_values[1], intervals, 0)
    self.assert_exclusively_in(grid_values[2], intervals, 1)
    self.assert_exclusively_in(grid_values[3], intervals, 1)
    self.assert_exclusively_in(grid_values[4], intervals, 2)
    self.assert_exclusively_in(grid_values[5], intervals, 2)

    intervals = segmenter.segmented_intervals(parameter, 1)
    assert len(intervals) == 1
    assert len([i for i in intervals if size(i) == 6]) == 1
    for qv in grid_values:
      self.assert_exclusively_in(qv, intervals, 0)

    intervals = segmenter.segmented_intervals(parameter, 10)
    assert len(intervals) == 10
    assert len([i for i in intervals if size(i) == 1]) == 6
    assert len([i for i in intervals if size(i) == 0]) == 4
    self.assert_exclusively_in(grid_values[0], intervals, 0)
    self.assert_exclusively_in(grid_values[5], intervals, 9)

  def test_latin_hypercube_grid_parameter_uneven_spacing(self, segmenter):
    grid_values = [0.1, 0.2, 0.4, 0.6, 1.0, 1.8]

    def size(interval):
      return len([v for v in grid_values if v in interval])

    parameter = self.double_parameter(0, 1, grid=grid_values)

    intervals = segmenter.segmented_intervals(parameter, 3)
    assert len(intervals) == 3
    assert len([i for i in intervals if size(i) == 2]) == 3
    self.assert_exclusively_in(grid_values[0], intervals, 0)
    self.assert_exclusively_in(grid_values[1], intervals, 0)
    self.assert_exclusively_in(grid_values[2], intervals, 1)
    self.assert_exclusively_in(grid_values[3], intervals, 1)
    self.assert_exclusively_in(grid_values[4], intervals, 2)
    self.assert_exclusively_in(grid_values[5], intervals, 2)

    intervals = segmenter.segmented_intervals(parameter, 1)
    assert len(intervals) == 1
    assert len([i for i in intervals if size(i) == 6]) == 1
    for qv in grid_values:
      self.assert_exclusively_in(qv, intervals, 0)

    intervals = segmenter.segmented_intervals(parameter, 10)
    assert len(intervals) == 10
    assert len([i for i in intervals if size(i) == 1]) == 6
    assert len([i for i in intervals if size(i) == 0]) == 4
    self.assert_exclusively_in(grid_values[0], intervals, 0)
    self.assert_exclusively_in(grid_values[5], intervals, 9)

  def test_double_has_values(self, segmenter):
    p = ExperimentParameter(param_type=PARAMETER_DOUBLE)
    p = ExperimentParameterProxy(p)
    assert segmenter.has_values(p, ClosedInterval(1, 1))
    assert not segmenter.has_values(p, LeftOpenInterval(1, 1))
    assert not segmenter.has_values(p, RightOpenInterval(1, 1))
    assert not segmenter.has_values(p, OpenInterval(1, 1))

    assert segmenter.has_values(p, ClosedInterval(1, 2))
    assert segmenter.has_values(p, LeftOpenInterval(1, 2))
    assert segmenter.has_values(p, RightOpenInterval(1, 2))
    assert segmenter.has_values(p, OpenInterval(1, 2))

    assert not segmenter.has_values(p, ClosedInterval(3, 2))
    assert not segmenter.has_values(p, LeftOpenInterval(3, 2))
    assert not segmenter.has_values(p, RightOpenInterval(3, 2))
    assert not segmenter.has_values(p, OpenInterval(3, 2))

  def test_categorical_has_values(self, segmenter):
    p = ExperimentParameter(param_type=PARAMETER_CATEGORICAL)
    p = ExperimentParameterProxy(p)
    cv = ExperimentCategoricalValue(enum_index=0)
    cv2 = ExperimentCategoricalValue(enum_index=1)
    assert not segmenter.has_values(p, [])
    assert segmenter.has_values(p, [cv])
    assert segmenter.has_values(p, [cv, cv2])

  def test_grid_has_values(self, segmenter):
    p = ExperimentParameter(param_type=PARAMETER_DOUBLE)
    p = ExperimentParameterProxy(p)
    qv = 0.1
    qv2 = 0.314
    assert not segmenter.has_values(p, [])
    assert segmenter.has_values(p, [qv])
    assert segmenter.has_values(p, [qv, qv2])

  def test_int_has_values(self, segmenter):
    p = ExperimentParameter(param_type=PARAMETER_INT)
    p = ExperimentParameterProxy(p)
    assert segmenter.has_values(p, ClosedInterval(1, 1))
    assert not segmenter.has_values(p, LeftOpenInterval(1, 1))
    assert not segmenter.has_values(p, RightOpenInterval(1, 1))
    assert not segmenter.has_values(p, OpenInterval(1, 1))

    assert segmenter.has_values(p, ClosedInterval(1, 2))
    assert segmenter.has_values(p, LeftOpenInterval(1, 2))
    assert segmenter.has_values(p, RightOpenInterval(1, 2))
    assert not segmenter.has_values(p, OpenInterval(1, 2))

    assert segmenter.has_values(p, ClosedInterval(1, 1.5))
    assert not segmenter.has_values(p, LeftOpenInterval(1, 1.5))
    assert segmenter.has_values(p, RightOpenInterval(1, 1.5))
    assert not segmenter.has_values(p, OpenInterval(1, 1.5))

    assert segmenter.has_values(p, ClosedInterval(1.5, 2))
    assert segmenter.has_values(p, LeftOpenInterval(1.5, 2))
    assert not segmenter.has_values(p, RightOpenInterval(1.5, 2))
    assert not segmenter.has_values(p, OpenInterval(1.5, 2))

    assert not segmenter.has_values(p, ClosedInterval(3, 2))
    assert not segmenter.has_values(p, LeftOpenInterval(3, 2))
    assert not segmenter.has_values(p, RightOpenInterval(3, 2))
    assert not segmenter.has_values(p, OpenInterval(3, 2))

    assert not segmenter.has_values(p, ClosedInterval(1.5, 1.5))
    assert not segmenter.has_values(p, LeftOpenInterval(1.5, 1.5))
    assert not segmenter.has_values(p, RightOpenInterval(1.5, 1.5))
    assert not segmenter.has_values(p, OpenInterval(1.5, 1.5))

    assert not segmenter.has_values(p, ClosedInterval(1.1, 1.9))
    assert not segmenter.has_values(p, LeftOpenInterval(1.1, 1.9))
    assert not segmenter.has_values(p, RightOpenInterval(1.1, 1.9))
    assert not segmenter.has_values(p, OpenInterval(1.1, 1.9))

    assert segmenter.has_values(p, ClosedInterval(1.9, 2.1))
    assert segmenter.has_values(p, LeftOpenInterval(1.9, 2.1))
    assert segmenter.has_values(p, RightOpenInterval(1.9, 2.1))
    assert segmenter.has_values(p, OpenInterval(1.9, 2.1))

  def test_categorical_only(self, segmenter):
    num_values = 6

    p1 = self.categorical_parameter(
      [
        ExperimentCategoricalValue(enum_index=0),
        ExperimentCategoricalValue(enum_index=1),
        ExperimentCategoricalValue(enum_index=2),
      ]
    )
    p2 = self.categorical_parameter(
      [
        ExperimentCategoricalValue(enum_index=0),
        ExperimentCategoricalValue(enum_index=1),
      ]
    )
    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[p1.copy_protobuf(), p2.copy_protobuf()],
      )
    )
    observations = []
    services = self.mock_services(segmenter, observations)

    sampler = CategoricalOnlySampler(services, experiment, partial_opt_args())
    multi_suggestions = sampler.fetch_best_suggestions(num_values)
    multi_observations = [self.suggestion_to_observation(experiment, s) for s in multi_suggestions]

    for _ in range(num_values):
      optimization_args = partial_opt_args(observation_iterator=observations, observation_count=len(observations))
      sampler = CategoricalOnlySampler(services, experiment, optimization_args)
      suggestion = sampler.fetch_best_suggestions(1)[0]  # pylint: disable=unsubscriptable-object
      observations.append(self.suggestion_to_observation(experiment, suggestion))

    for check in (observations, multi_observations):
      assert len(set(check)) == len(check)
      assert len(set(check)) == num_values

      assert any(((o.get_assignment(p1) == 0 and o.get_assignment(p2) == 0 for o in check)))
      assert any(((o.get_assignment(p1) == 1 and o.get_assignment(p2) == 0 for o in check)))
      assert any(((o.get_assignment(p1) == 2 and o.get_assignment(p2) == 0 for o in check)))
      assert any(((o.get_assignment(p1) == 0 and o.get_assignment(p2) == 1 for o in check)))
      assert any(((o.get_assignment(p1) == 1 and o.get_assignment(p2) == 1 for o in check)))
      assert any(((o.get_assignment(p1) == 2 and o.get_assignment(p2) == 1 for o in check)))

    suggestions = []
    del observations[0 : len(observations)]
    assert services.observation_service.all_data(experiment) == []

    for _ in range(num_values):
      optimization_args = partial_opt_args(open_suggestions=suggestions)
      sampler = CategoricalOnlySampler(services, experiment, optimization_args)
      suggestion = sampler.fetch_best_suggestions(1)[0]  # pylint: disable=unsubscriptable-object
      suggestions.append(suggestion)
    observations = [self.suggestion_to_observation(experiment, s) for s in suggestions]

    for check in (observations, multi_observations):
      assert len(set(check)) == len(check)
      assert len(set(check)) == num_values
      assert any(((o.get_assignment(p1) == 0 and o.get_assignment(p2) == 0 for o in check)))
      assert any(((o.get_assignment(p1) == 1 and o.get_assignment(p2) == 0 for o in check)))
      assert any(((o.get_assignment(p1) == 2 and o.get_assignment(p2) == 0 for o in check)))
      assert any(((o.get_assignment(p1) == 0 and o.get_assignment(p2) == 1 for o in check)))
      assert any(((o.get_assignment(p1) == 1 and o.get_assignment(p2) == 1 for o in check)))
      assert any(((o.get_assignment(p1) == 2 and o.get_assignment(p2) == 1 for o in check)))

  @pytest.mark.parametrize(
    "suggestion_number,expected_assignments",
    [
      (0, (0, 3, 0)),
      (1, (0, 3, 0)),
      (2, (1, 3, 0)),
      (3, (1, 3, 0)),
      (4, (2, 3, 0)),
      (5, (0, 3.1, 0)),
      (10, (0, 5, 0)),
      (15, (0, 3, 5)),
      (20, (0, 3.1, 5)),
      (23, (1, 3.1, 5)),
      (25, (0, 5, 5)),
      (30, (0, 3, 10)),
      (44, (2, 5, 10)),
    ],
  )
  def test_explicit_grid(self, services, suggestion_number, expected_assignments):
    categorical_parameter = self.categorical_parameter(
      [
        ExperimentCategoricalValue(enum_index=0),
        ExperimentCategoricalValue(enum_index=1),
        ExperimentCategoricalValue(enum_index=2),
      ],
      grid=[0, 0, 1, 1, 2],
    )
    double_parameter = self.double_parameter(3, 5, grid=[3, 3.1, 5])
    int_parameter = self.int_parameter(0, 10, grid=[0, 5, 10])

    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          int_parameter.copy_protobuf(),
          double_parameter.copy_protobuf(),
          categorical_parameter.copy_protobuf(),
        ],
      ),
    )

    sampler = GridSampler(services, experiment, partial_opt_args())
    suggestion = sampler.get_suggestion(suggestion_number)
    categorical_assignment = suggestion.get_assignment(categorical_parameter)
    double_assignment = suggestion.get_assignment(double_parameter)
    int_assignment = suggestion.get_assignment(int_parameter)
    assert (categorical_assignment, double_assignment, int_assignment) == expected_assignments

  # NOTE: This test has about 1% chance of failing, hence marking it flaky.
  @flaky(max_runs=2)
  def test_random_sampler_log_transform(self, segmenter):
    double_parameter = self.double_parameter(1e-5, 1, log_scale=True)
    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[double_parameter.copy_protobuf()],
      ),
    )

    observations = []
    services = self.mock_services(segmenter, observations)
    sampler = RandomSampler(services, experiment, UnprocessedSuggestion.Source.EXPLICIT_RANDOM)
    multi_suggestions = sampler.generate_random_suggestions(10)
    for suggestion in multi_suggestions:
      assert suggestion.get_assignment(double_parameter) in ClosedInterval(1e-5, 1)

    # test suggestions are from a uniform distribution in the log space
    multi_suggestions = sampler.generate_random_suggestions(100)
    loguniform_rvs = [s.get_assignment(double_parameter) for s in multi_suggestions]
    assert stats.kstest(numpy.log10(loguniform_rvs), stats.uniform(-5, 5).cdf).pvalue > 0.01

  def test_random_sampler_grid(self, segmenter):
    grid_values = [-2, -0.3, 0, 0.0001, 0.02, 23]
    grid_parameter = self.double_parameter(0, 1, grid=grid_values)
    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[grid_parameter.copy_protobuf()],
      ),
    )

    observations = []
    services = self.mock_services(segmenter, observations)
    sampler = RandomSampler(services, experiment, UnprocessedSuggestion.Source.EXPLICIT_RANDOM)
    multi_suggestions = sampler.generate_random_suggestions(15)
    for suggestion in multi_suggestions:
      assert suggestion.get_assignment(grid_parameter) in grid_values

  def test_random_sampler_categorical_delete(self, segmenter):
    real_values = [
      ExperimentCategoricalValue(enum_index=0),
      ExperimentCategoricalValue(enum_index=2),
    ]
    deleted_value = ExperimentCategoricalValue(enum_index=1, deleted=True)
    parameter = self.categorical_parameter(real_values + [deleted_value])
    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[parameter.copy_protobuf()],
      ),
    )

    observations = []
    services = self.mock_services(segmenter, observations)
    sampler = RandomSampler(services, experiment, UnprocessedSuggestion.Source.EXPLICIT_RANDOM)
    multi_suggestions = sampler.generate_random_suggestions(15)
    for suggestion in multi_suggestions:
      assert suggestion.get_assignment(parameter) in [0, 2]

  def test_conditionals(self, segmenter):
    # pylint: disable=too-many-locals,too-many-statements
    conditional_parameter = self.conditional_parameter(
      "x",
      [
        ExperimentConditionalValue(name="1", enum_index=1),
        ExperimentConditionalValue(name="2", enum_index=2),
      ],
    )
    categorical_parameter = self.categorical_parameter(
      [
        ExperimentCategoricalValue(enum_index=0),
        ExperimentCategoricalValue(enum_index=1),
        ExperimentCategoricalValue(enum_index=2),
      ],
      conditions=[ParameterCondition(name="x", values=[1, 2])],
    )
    double_parameter = self.double_parameter(0, 1, conditions=[ParameterCondition(name="x", values=[1])])
    int_parameter = self.int_parameter(1, 10)

    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          int_parameter.copy_protobuf(),
          double_parameter.copy_protobuf(),
          categorical_parameter.copy_protobuf(),
        ],
        conditionals=[conditional_parameter.copy_protobuf()],  # pylint: disable=protobuf-undefined-attribute
      ),
    )

    observations = []
    services = self.mock_services(segmenter, observations)
    sampler = LatinHypercubeSampler(services, experiment, partial_opt_args())
    assert not sampler.experiment.conditionals
    assert len(sampler.experiment.experiment_meta.all_parameters_unsorted) == 4

    stencil_length = get_low_discrepancy_stencil_length_from_experiment(sampler.experiment)
    multi_suggestions = sampler.fetch_best_suggestions(stencil_length)
    for suggestion in multi_suggestions:
      if suggestion.get_conditional_assignments(experiment) == {"x": 1}:
        assert suggestion.get_assignment(double_parameter) in ClosedInterval(0, 1)
        assert len(suggestion.get_assignments(experiment)) == 4
      else:
        has_assignments = suggestion.suggestion_meta.suggestion_data.copy_protobuf()
        values_dict = has_assignments.assignments_map
        assert double_parameter.name not in values_dict
        assert len(suggestion.get_assignments(experiment)) == 3
      assert suggestion.get_assignment(int_parameter) in range(1, 11)
      assert suggestion.get_assignment(categorical_parameter) in [0, 1, 2]

    for k in range(stencil_length):
      optimization_args = partial_opt_args(observation_iterator=observations, observation_count=len(observations))
      sampler = LatinHypercubeSampler(services, experiment, optimization_args)
      suggestion = sampler.fetch_best_suggestions(1)[0]
      observations.append(self.suggestion_to_observation(experiment, suggestion, id_num=k))

      if suggestion.get_conditional_assignments(experiment) == {"x": 1}:
        assert suggestion.get_assignment(double_parameter) in ClosedInterval(0, 1)
        assert len(suggestion.get_assignments(experiment)) == 4
      else:
        assert len(suggestion.get_assignments(experiment)) == 3
      assert suggestion.get_assignment(int_parameter) in range(1, 11)
      assert suggestion.get_assignment(categorical_parameter) in [0, 1, 2]

    # Even if the stencil length is exhausted, sampler should still return a LHC suggestion
    optimization_args = partial_opt_args(observation_iterator=observations, observation_count=len(observations))
    sampler = LatinHypercubeSampler(services, experiment, optimization_args)
    suggestions = sampler.fetch_best_suggestions(1)
    assert len(suggestions) == 1
    assert suggestions[0].source == UnprocessedSuggestion.Source.LATIN_HYPERCUBE

    # Test RandomSampler for conditionals
    sampler = RandomSampler(services, experiment, UnprocessedSuggestion.Source.EXPLICIT_RANDOM)
    assert not sampler.experiment.conditionals
    assert len(sampler.experiment.experiment_meta.all_parameters_unsorted) == 4

    multi_suggestions = sampler.generate_random_suggestions(3)
    for suggestion in multi_suggestions:
      if suggestion.get_conditional_assignments(experiment) == {"x": 1}:
        assert suggestion.get_assignment(double_parameter) in ClosedInterval(0, 1)
        assert len(suggestion.get_assignments(experiment)) == 4
      else:
        has_assignments = suggestion.suggestion_meta.suggestion_data.copy_protobuf()
        values_dict = has_assignments.assignments_map
        assert double_parameter.name not in values_dict
        assert len(suggestion.get_assignments(experiment)) == 3
      assert suggestion.get_assignment(int_parameter) in range(1, 11)
      assert suggestion.get_assignment(categorical_parameter) in [0, 1, 2]
