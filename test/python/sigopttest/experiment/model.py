# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.experiment.model import Experiment, ExperimentParameterProxy
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *


class TestValidAssignmentCategorical(object):
  @pytest.fixture
  def parameter(self):
    parameter = ExperimentParameter(
      name="categorical_param",
      param_type=PARAMETER_CATEGORICAL,
    )
    for idx, name in enumerate(["a", "b", "c"], start=1):
      parameter.all_categorical_values.add(enum_index=idx, name=name)
    parameter.all_categorical_values.add(enum_index=4, name="d", deleted=True)
    return ExperimentParameterProxy(parameter)

  @pytest.mark.parametrize("assignment", [1, 2, 3])
  def test_active_values(self, parameter, assignment):
    assert parameter.valid_assignment(assignment) is True

  def test_deleted_categorical_value(self, parameter):
    assert parameter.valid_assignment(4) is False

  @pytest.mark.parametrize("assignment", ["a", "b", "c", "d", 0, 5, 6, -1])
  def invalid_assignment(self, parameter, assignment):
    assert parameter.valid_assignment(assignment) is False


class TestValidAssignmentNumerical(object):
  @pytest.fixture(params=[PARAMETER_DOUBLE, PARAMETER_INT])
  def parameter(self, request):
    parameter = ExperimentParameter(
      name="numerical_param",
      param_type=request.param,
    )
    parameter.bounds.minimum = -1
    parameter.bounds.maximum = 3
    return ExperimentParameterProxy(parameter)

  @pytest.mark.parametrize("assignment", [-1, 0, 1, 2, 3, -0.9, 1.6666])
  def test_in_bounds(self, parameter, assignment):
    assert parameter.valid_assignment(assignment) is True

  @pytest.mark.parametrize("assignment", [-50, -2, 4, 67, -1.5, 67.999999])
  def test_out_of_bounds(self, parameter, assignment):
    assert parameter.valid_assignment(assignment) is False


class TestExperimentModel(object):
  def test_conditionals_breadth_empty(self):
    meta = ExperimentMeta()
    experiment = Experiment(experiment_meta=meta)
    assert experiment.conditionals_breadth == 0

  def test_conditionals_breadth(self):
    meta = ExperimentMeta()
    for _ in range(3):
      meta.conditionals.add()

    meta.conditionals[0].values.add()
    meta.conditionals[1].values.add()
    meta.conditionals[1].values.add()

    experiment = Experiment(experiment_meta=meta)
    assert experiment.conditionals_breadth == 3

  def test_is_search_default_false(self):
    meta = ExperimentMeta()
    experiment = Experiment(experiment_meta=meta)
    assert experiment.is_search is False

  def test_is_search_experiment_with_optimization(self):
    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        metrics=[ExperimentMetric(name="metric_1", objective=MINIMIZE, threshold=2.5)],
      )
    )
    assert experiment.is_search is False

  @pytest.mark.parametrize("num_contraints", [1, 4])
  def test_is_search_experiment_with_all_constraints(self, num_contraints):
    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        metrics=[
          ExperimentMetric(name=f"c_{i}", strategy=ExperimentMetric.CONSTRAINT, threshold=4.5)
          for i in range(num_contraints)
        ],
      )
    )
    assert experiment.is_search is True
    assert len(experiment.metric_thresholds) == num_contraints

  @pytest.mark.parametrize("extra_metric_strategy", [ExperimentMetric.CONSTRAINT, ExperimentMetric.STORE])
  def test_is_search_experiment_with_all_constraints_and_extra_metric(self, extra_metric_strategy):
    experiment = Experiment(
      experiment_meta=ExperimentMeta(
        metrics=[
          ExperimentMetric(name="c_0", strategy=ExperimentMetric.CONSTRAINT, threshold=4.5),
          ExperimentMetric(name="extra", strategy=extra_metric_strategy),
        ],
      )
    )
    assert experiment.is_search is True


class TestMetricThresholds(object):
  @pytest.mark.parametrize("threshold_1", [None, 0.0, 4.5])
  def test_access_metric_thresholds_no_multimetric(self, threshold_1):
    e = Experiment(
      experiment_meta=ExperimentMeta(
        metrics=[ExperimentMetric(name="metric_1", threshold=threshold_1)],
      )
    )
    assert e.metric_thresholds == [threshold_1]

  def test_access_metric_thresholds_no_multimetric_or_threshold(self):
    e = Experiment(
      experiment_meta=ExperimentMeta(
        metrics=[
          ExperimentMetric(
            name="metric_1",
          )
        ],
      )
    )
    assert e.metric_thresholds == [None]

  def test_access_no_metric_thresholds(self):
    e = Experiment(
      experiment_meta=ExperimentMeta(
        metrics=[
          ExperimentMetric(
            name="metric_1",
          ),
          ExperimentMetric(
            name="metric_2",
            objective=MAXIMIZE,
          ),
        ],
      )
    )
    assert e.metric_thresholds == [None, None]

  @pytest.mark.parametrize("threshold_1", [None, 0.0, 11.6])
  @pytest.mark.parametrize("threshold_2", [None, -2.123456789, 0.0])
  def test_access_metric_thresholds(self, threshold_1, threshold_2):
    e = Experiment(
      experiment_meta=ExperimentMeta(
        metrics=[
          ExperimentMetric(name="metric_1", objective=MAXIMIZE, threshold=threshold_1),
          ExperimentMetric(name="metric_2", objective=MINIMIZE, threshold=threshold_2),
        ],
      )
    )
    assert e.metric_thresholds == [threshold_1, threshold_2]

  @pytest.mark.parametrize("threshold_1", [None, 0.0, 11.6])
  @pytest.mark.parametrize("threshold_2", [None, -2.123456789, 0.0])
  @pytest.mark.parametrize("threshold_3", [None, 1.0])
  @pytest.mark.parametrize("strategy_2", [ExperimentMetric.CONSTRAINT, ExperimentMetric.OPTIMIZE])
  @pytest.mark.parametrize("strategy_3", [ExperimentMetric.CONSTRAINT, ExperimentMetric.STORE])
  def test_access_metric_constraints(self, threshold_1, threshold_2, threshold_3, strategy_2, strategy_3):
    e = Experiment(
      experiment_meta=ExperimentMeta(
        metrics=[
          ExperimentMetric(name="metric_1", objective=MAXIMIZE, threshold=threshold_1),
          ExperimentMetric(
            name="metric_2",
            objective=MINIMIZE,
            threshold=threshold_2,
            strategy=strategy_2,
          ),
          ExperimentMetric(
            name="metric_3",
            objective=MAXIMIZE,
            threshold=threshold_3,
            strategy=strategy_3,
          ),
        ],
      )
    )
    assert e.metric_thresholds == [threshold_1, threshold_2, threshold_3]


class TestModelConstrainedExperimentProperties(object):
  def test_model_constrained_experiment_properties(self):
    dim = 10
    n_constrained_doubles = 5
    all_parameters_unsorted = []
    for i in range(dim):
      all_parameters_unsorted.append(
        ExperimentParameter(
          name=f"double_{i}",
          bounds=Bounds(minimum=0, maximum=1),
          param_type=PARAMETER_DOUBLE,
        ),
      )
      all_parameters_unsorted.append(
        ExperimentParameter(
          name=f"int_{i}",
          bounds=Bounds(minimum=0, maximum=10),
          param_type=PARAMETER_INT,
        ),
      )
      all_parameters_unsorted.append(
        ExperimentParameter(
          name=f"cat_{i}",
          all_categorical_values=[
            ExperimentCategoricalValue(name="a", enum_index=1),
            ExperimentCategoricalValue(name="b", enum_index=2),
            ExperimentCategoricalValue(name="c", enum_index=3),
          ],
          param_type=PARAMETER_CATEGORICAL,
        ),
      )
    constraints = [
      ExperimentConstraint(
        type="less_than",
        terms=[Term(name=f"double_{i}", coeff=1) for i in range(n_constrained_doubles - 1)],
        rhs=1,
      ),
      ExperimentConstraint(
        type="less_than",
        terms=[Term(name=f"double_{i}", coeff=i + 1) for i in range(n_constrained_doubles)],
        rhs=1,
      ),
    ]
    experiment_meta = ExperimentMeta(all_parameters_unsorted=all_parameters_unsorted, constraints=constraints)
    experiment = Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=experiment_meta,
    )
    assert experiment.has_constraints is True
    assert experiment.halfspaces.shape[1] == n_constrained_doubles + 1
    double_constrained_param_names = [f"double_{i}" for i in range(n_constrained_doubles)]
    for parameter in experiment.constrained_parameters:
      assert parameter.name in double_constrained_param_names
    unconstrained_parameter_names = []
    for i in range(dim):
      unconstrained_parameter_names.append(f"int_{i}")
      unconstrained_parameter_names.append(f"cat_{i}")
    for i in range(n_constrained_doubles, dim):
      unconstrained_parameter_names.append(f"double_{i}")
    for parameter in experiment.unconstrained_parameters:
      assert parameter.name in unconstrained_parameter_names
