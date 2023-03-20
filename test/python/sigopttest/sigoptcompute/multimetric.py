# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest

from zigopt.experiment.model import Experiment
from zigopt.observation.model import Observation
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  MINIMIZE,
  Bounds,
  ExperimentMeta,
  ExperimentMetric,
  ExperimentParameter,
)
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData, ObservationValue
from zigopt.sigoptcompute.adapter import SCAdapter

from sigoptaux.adapter_info_containers import MetricsInfo
from sigoptaux.constant import MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD
from sigoptaux.multimetric import find_pareto_frontier_observations_for_maximization
from sigopttest.optimize.sources.base_test import UnitTestBase


class TestMultimetric(UnitTestBase):
  def test_find_pareto_frontier_observations_for_maximization(self):
    values = [[0, 1], [1, 2], [3, 4], [4, 3]]
    observations = [Observation(id=k) for k, _ in enumerate(values)]
    pf, npf = find_pareto_frontier_observations_for_maximization(values, observations)
    assert {o.id for o in pf} == {2, 3} and {o.id for o in npf} == {0, 1}

  def test_multimetric_value(self):
    experiment = Experiment(
      experiment_meta=ExperimentMeta(metrics=[ExperimentMetric(name="f"), ExperimentMetric(name="g")])
    )
    observation = Observation(
      data=ObservationData(
        values=[ObservationValue(name="f", value=5), ObservationValue(name="g", value=6)],
      )
    )
    assert observation.data.sorted_all_metric_values(experiment) == [5, 6]

    observation = Observation(
      data=ObservationData(
        values=[ObservationValue(name="g", value=6), ObservationValue(name="f", value=5)],
      )
    )
    assert observation.data.sorted_all_metric_values(experiment) == [5, 6]

    experiment = Experiment(
      experiment_meta=ExperimentMeta(metrics=[ExperimentMetric(name="g"), ExperimentMetric(name="f")])
    )
    assert observation.data.sorted_all_metric_values(experiment) == [5, 6]

    # NOTE: Can we even have this situation?  We handle it as a failure (fine) but could this occur?
    observation = Observation(
      data=ObservationData(
        values=[ObservationValue(name="f"), ObservationValue(name="g", value=6)],
      )
    )
    assert observation.data.sorted_all_metric_values(experiment) is None

    observation = Observation(data=ObservationData(values=[ObservationValue(name="g", value=6)]))
    with pytest.raises(AssertionError):
      observation.data.sorted_all_metric_values(experiment)

    experiment = Experiment(experiment_meta=ExperimentMeta(metrics=[ExperimentMetric(name="f")]))
    observation = Observation(
      data=ObservationData(
        values=[ObservationValue(name="g", value=6), ObservationValue(name="f", value=5)],
      )
    )
    with pytest.raises(AssertionError):
      observation.data.sorted_all_metric_values(experiment)

    observation = Observation(data=ObservationData(values=[ObservationValue(name="f", value=5)]))
    assert observation.data.sorted_all_metric_values(experiment) == [5]

    observation = Observation(data=ObservationData(values=[ObservationValue(value=5)]))
    assert observation.data.sorted_all_metric_values(experiment) == [5]

    observation = Observation(data=ObservationData(values=[ObservationValue()]))
    assert observation.data.sorted_all_metric_values(experiment) is None

    observation = Observation(data=ObservationData())
    assert observation.data.sorted_all_metric_values(experiment) is None

  def test_multimetric_value_var(self):
    experiment = Experiment(
      experiment_meta=ExperimentMeta(metrics=[ExperimentMetric(name="f"), ExperimentMetric(name="g")])
    )
    observation = Observation(
      data=ObservationData(
        values=[ObservationValue(name="f", value_var=5), ObservationValue(name="g", value_var=6)],
      )
    )
    assert observation.data.sorted_all_metric_value_vars(experiment) == [5, 6]

    observation = Observation(
      data=ObservationData(
        values=[ObservationValue(name="g", value_var=6), ObservationValue(name="f", value_var=5)],
      )
    )
    assert observation.data.sorted_all_metric_value_vars(experiment) == [5, 6]

    experiment = Experiment(
      experiment_meta=ExperimentMeta(metrics=[ExperimentMetric(name="g"), ExperimentMetric(name="f")])
    )
    assert observation.data.sorted_all_metric_value_vars(experiment) == [5, 6]

    observation = Observation(
      data=ObservationData(
        values=[ObservationValue(name="f"), ObservationValue(name="g", value_var=6)],
      )
    )
    assert observation.data.sorted_all_metric_value_vars(experiment) is None

    observation = Observation(data=ObservationData(values=[ObservationValue(name="g", value_var=6)]))
    with pytest.raises(AssertionError):
      observation.data.sorted_all_metric_value_vars(experiment)

    experiment = Experiment(experiment_meta=ExperimentMeta(metrics=[ExperimentMetric(name="f")]))
    observation = Observation(
      data=ObservationData(
        values=[ObservationValue(name="g", value_var=6), ObservationValue(name="f", value_var=5)],
      )
    )
    with pytest.raises(AssertionError):
      observation.data.sorted_all_metric_value_vars(experiment)

    observation = Observation(data=ObservationData(values=[ObservationValue(name="f", value_var=5)]))
    assert observation.data.sorted_all_metric_value_vars(experiment) == [5]

    observation = Observation(data=ObservationData(values=[ObservationValue(value_var=5)]))
    assert observation.data.sorted_all_metric_value_vars(experiment) == [5]

    observation = Observation(data=ObservationData(values=[ObservationValue()]))
    assert observation.data.sorted_all_metric_value_vars(experiment) is None

    observation = Observation(data=ObservationData())
    assert observation.data.sorted_all_metric_value_vars(experiment) is None

  def test_form_metrics_info(self):
    meta = ExperimentMeta(metrics=[ExperimentMetric(name="f", objective=MINIMIZE)])
    meta.observation_budget = numpy.random.randint(50, 200)
    singlemetric_test_experiment = Experiment(experiment_meta=meta)
    metrics_info = SCAdapter.form_metrics_info(singlemetric_test_experiment)
    expected_metrics_info = MetricsInfo(
      requires_pareto_frontier_optimization=False,
      observation_budget=meta.observation_budget,
      user_specified_thresholds=[None],
      objectives=["minimize"],
      optimized_metrics_index=[0],
      constraint_metrics_index=[],
    )
    assert expected_metrics_info == metrics_info
    assert metrics_info.has_optimization_metrics
    assert not metrics_info.has_constraint_metrics
    assert not metrics_info.has_optimized_metric_thresholds

    meta.metrics.add()
    meta.observation_budget = numpy.random.randint(50, 200)
    metrics_test_experiment = Experiment(experiment_meta=meta)
    metrics_info = SCAdapter.form_metrics_info(metrics_test_experiment)
    expected_metrics_info = MetricsInfo(
      requires_pareto_frontier_optimization=True,
      observation_budget=meta.observation_budget,
      user_specified_thresholds=[None, None],
      objectives=["maximize", "minimize"],
      optimized_metrics_index=[0, 1],
      constraint_metrics_index=[],
    )
    assert expected_metrics_info == metrics_info
    assert metrics_info.has_optimization_metrics
    assert not metrics_info.has_constraint_metrics
    assert not metrics_info.has_optimized_metric_thresholds

    metric_thresholds_meta = ExperimentMeta(
      metrics=[
        ExperimentMetric(name="h", threshold=0.5),
        ExperimentMetric(name="f", threshold=1.3),
        ExperimentMetric(name="g", strategy=ExperimentMetric.STORE),
      ]
    )
    metric_thresholds_meta.observation_budget = numpy.random.randint(50, 200)
    metric_thresholds_test_experiment = Experiment(experiment_meta=metric_thresholds_meta)
    metrics_info = SCAdapter.form_metrics_info(metric_thresholds_test_experiment)
    expected_metrics_info = MetricsInfo(
      requires_pareto_frontier_optimization=True,
      observation_budget=metric_thresholds_meta.observation_budget,
      user_specified_thresholds=[1.3, None, 0.5],
      objectives=["maximize", "maximize", "maximize"],
      optimized_metrics_index=[0, 2],
      constraint_metrics_index=[],
    )
    assert expected_metrics_info == metrics_info
    assert metrics_info.has_optimization_metrics
    assert not metrics_info.has_constraint_metrics
    assert metrics_info.has_optimized_metric_thresholds

    metric_constraints_meta = ExperimentMeta(
      metrics=[
        ExperimentMetric(name="h", objective=MINIMIZE),
        ExperimentMetric(name="f", threshold=1.3),
        ExperimentMetric(name="g", strategy=ExperimentMetric.STORE),
        ExperimentMetric(name="e", threshold=0.0, objective=MINIMIZE, strategy=ExperimentMetric.CONSTRAINT),
      ]
    )
    metric_constraints_meta.observation_budget = numpy.random.randint(50, 200)
    metric_constraints_test_experiment = Experiment(experiment_meta=metric_constraints_meta)
    metrics_info = SCAdapter.form_metrics_info(metric_constraints_test_experiment)
    expected_metrics_info = MetricsInfo(
      requires_pareto_frontier_optimization=True,
      observation_budget=metric_constraints_meta.observation_budget,
      user_specified_thresholds=[0.0, 1.3, None, None],
      objectives=["minimize", "maximize", "maximize", "minimize"],
      optimized_metrics_index=[1, 3],
      constraint_metrics_index=[0],
    )
    assert expected_metrics_info == metrics_info
    assert metrics_info.has_optimization_metrics
    assert metrics_info.has_constraint_metrics
    assert metrics_info.has_optimized_metric_thresholds

    search_meta = ExperimentMeta(
      metrics=[
        ExperimentMetric(name="f", threshold=1.3, strategy=ExperimentMetric.CONSTRAINT),
        ExperimentMetric(name="g", strategy=ExperimentMetric.STORE),
        ExperimentMetric(name="e", threshold=0.0, objective=MINIMIZE, strategy=ExperimentMetric.CONSTRAINT),
      ]
    )
    search_meta.observation_budget = numpy.random.randint(50, 200)
    search_test_experiment = Experiment(experiment_meta=search_meta)
    metrics_info = SCAdapter.form_metrics_info(search_test_experiment)
    expected_metrics_info = MetricsInfo(
      requires_pareto_frontier_optimization=False,
      observation_budget=search_meta.observation_budget,
      user_specified_thresholds=[0.0, 1.3, None],
      objectives=["minimize", "maximize", "maximize"],
      optimized_metrics_index=[],
      constraint_metrics_index=[0, 1],
    )
    assert expected_metrics_info == metrics_info
    assert not metrics_info.has_optimization_metrics
    assert metrics_info.has_constraint_metrics
    assert not metrics_info.has_optimized_metric_thresholds


class TestFormMetricsInfoSearchNextPoints(UnitTestBase):
  def get_metrics_info_and_points_sampled_for_search_next_points(self, services, experiment):
    num_observations = numpy.random.randint(3, 9)
    suggestions = self.sample_suggestions(services, experiment, num_observations)
    observations = self.form_random_observations_from_suggestions(experiment, suggestions)
    # pylint: disable=protected-access
    points_sampled = SCAdapter._make_points_sampled(experiment, observations, num_observations)
    # pylint: enable=protected-access
    metrics_info = SCAdapter.form_metrics_info_for_search_next_point(experiment, points_sampled)
    return metrics_info, points_sampled

  def test_search_singlemetric(self, services):
    meta = ExperimentMeta(
      all_parameters_unsorted=[ExperimentParameter(name="x", bounds=Bounds(minimum=0.0, maximum=1.0))],
      metrics=[ExperimentMetric(name="f", threshold=0.0, objective=MINIMIZE, strategy=ExperimentMetric.CONSTRAINT)],
    )
    meta.observation_budget = numpy.random.randint(50, 200)

    singlemetric_search_experiment = Experiment(experiment_meta=meta)
    metrics_info, _ = self.get_metrics_info_and_points_sampled_for_search_next_points(
      services,
      singlemetric_search_experiment,
    )

    expected_metrics_info = MetricsInfo(
      requires_pareto_frontier_optimization=False,
      observation_budget=meta.observation_budget,
      user_specified_thresholds=[0.0],
      objectives=["minimize"],
      optimized_metrics_index=[],
      constraint_metrics_index=[0],
    )
    assert expected_metrics_info == metrics_info
    assert not metrics_info.has_optimization_metrics
    assert metrics_info.has_constraint_metrics
    assert not metrics_info.has_optimized_metric_thresholds

  def test_search_multimetric(self, services):
    search_meta = ExperimentMeta(
      all_parameters_unsorted=[ExperimentParameter(name="x", bounds=Bounds(minimum=0.0, maximum=1.0))],
      metrics=[
        ExperimentMetric(name="f", threshold=1.3, strategy=ExperimentMetric.CONSTRAINT),
        ExperimentMetric(name="g", strategy=ExperimentMetric.STORE),
        ExperimentMetric(name="e", threshold=0.0, objective=MINIMIZE, strategy=ExperimentMetric.CONSTRAINT),
      ],
    )
    search_meta.observation_budget = numpy.random.randint(50, 200)

    search_test_experiment = Experiment(experiment_meta=search_meta)
    metrics_info, _ = self.get_metrics_info_and_points_sampled_for_search_next_points(
      services,
      search_test_experiment,
    )

    expected_metrics_info = MetricsInfo(
      requires_pareto_frontier_optimization=False,
      observation_budget=search_meta.observation_budget,
      user_specified_thresholds=[0.0, 1.3, None],
      objectives=["minimize", "maximize", "maximize"],
      optimized_metrics_index=[],
      constraint_metrics_index=[0, 1],
    )
    assert expected_metrics_info == metrics_info
    assert not metrics_info.has_optimization_metrics
    assert metrics_info.has_constraint_metrics
    assert not metrics_info.has_optimized_metric_thresholds

  def test_multisolution_single_metric(self, services):
    meta = ExperimentMeta(
      all_parameters_unsorted=[ExperimentParameter(name="x", bounds=Bounds(minimum=0.0, maximum=1.0))],
      metrics=[ExperimentMetric(name="f", objective=MINIMIZE)],
    )
    meta.observation_budget = numpy.random.randint(50, 200)
    meta.num_solutions = 5

    single_opt_multisolution_experiment = Experiment(experiment_meta=meta)
    metrics_info, points_sampled = self.get_metrics_info_and_points_sampled_for_search_next_points(
      services,
      single_opt_multisolution_experiment,
    )

    expected_threshold = numpy.quantile(
      points_sampled.values[:, 0],
      1 - MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD,  # this is for minimization
    )
    expected_metrics_info = MetricsInfo(
      requires_pareto_frontier_optimization=False,
      observation_budget=meta.observation_budget,
      user_specified_thresholds=[expected_threshold],
      objectives=["minimize"],
      optimized_metrics_index=[],
      constraint_metrics_index=[0],
    )
    assert expected_metrics_info == metrics_info
    assert not metrics_info.has_optimization_metrics
    assert metrics_info.has_constraint_metrics
    assert not metrics_info.has_optimized_metric_thresholds

  def test_multisolution_multimetric_one_opt_one_constraint(self, services):
    meta = ExperimentMeta(
      all_parameters_unsorted=[ExperimentParameter(name="x", bounds=Bounds(minimum=0.0, maximum=1.0))],
      metrics=[
        ExperimentMetric(name="c", threshold=0.333, strategy=ExperimentMetric.CONSTRAINT),
        ExperimentMetric(name="a"),
        ExperimentMetric(name="b", strategy=ExperimentMetric.STORE),
      ],
    )
    meta.observation_budget = numpy.random.randint(50, 200)
    meta.num_solutions = numpy.random.randint(2, 10)

    one_opt_one_constraint_experiment = Experiment(experiment_meta=meta)
    metrics_info, points_sampled = self.get_metrics_info_and_points_sampled_for_search_next_points(
      services,
      one_opt_one_constraint_experiment,
    )

    expected_threshold = numpy.quantile(
      points_sampled.values[:, 0],
      MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD,
    )
    expected_metrics_info = MetricsInfo(
      observation_budget=meta.observation_budget,
      objectives=["maximize", "maximize", "maximize"],
      constraint_metrics_index=[0, 2],
      user_specified_thresholds=[expected_threshold, None, 0.333],
      optimized_metrics_index=[],
      requires_pareto_frontier_optimization=False,
    )
    assert expected_metrics_info == metrics_info
    assert not metrics_info.has_optimization_metrics
    assert metrics_info.has_constraint_metrics
    assert not metrics_info.has_optimized_metric_thresholds

  def test_multisolution_multimetric_one_opt_and_two_constraints(self, services):
    meta = ExperimentMeta(
      all_parameters_unsorted=[ExperimentParameter(name="x", bounds=Bounds(minimum=0.0, maximum=1.0))],
      metrics=[
        ExperimentMetric(name="b", objective=MINIMIZE),
        ExperimentMetric(name="d", threshold=0.444, strategy=ExperimentMetric.CONSTRAINT, objective=MINIMIZE),
        ExperimentMetric(name="a", threshold=0.111, strategy=ExperimentMetric.CONSTRAINT),
        ExperimentMetric(name="c", strategy=ExperimentMetric.STORE),
      ],
    )
    meta.observation_budget = numpy.random.randint(50, 200)
    meta.num_solutions = numpy.random.randint(2, 10)

    one_opt_two_constraint_experiment = Experiment(experiment_meta=meta)
    metrics_info, points_sampled = self.get_metrics_info_and_points_sampled_for_search_next_points(
      services,
      one_opt_two_constraint_experiment,
    )

    expected_threshold = numpy.quantile(
      points_sampled.values[:, 1],
      1 - MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD,  # objective is minimize
    )
    expected_metrics_info = MetricsInfo(
      observation_budget=meta.observation_budget,
      objectives=["maximize", "minimize", "maximize", "minimize"],
      constraint_metrics_index=[0, 1, 3],
      user_specified_thresholds=[0.111, expected_threshold, None, 0.444],
      optimized_metrics_index=[],
      requires_pareto_frontier_optimization=False,
    )
    assert expected_metrics_info == metrics_info
    assert not metrics_info.has_optimization_metrics
    assert metrics_info.has_constraint_metrics
    assert not metrics_info.has_optimized_metric_thresholds

  def test_multisolution_multimetric_one_opt_and_three_constraints(self, services):
    meta = ExperimentMeta(
      all_parameters_unsorted=[ExperimentParameter(name="x", bounds=Bounds(minimum=0.0, maximum=1.0))],
      metrics=[
        ExperimentMetric(name="d", threshold=0.222, strategy=ExperimentMetric.CONSTRAINT),
        ExperimentMetric(name="b", strategy=ExperimentMetric.STORE),
        ExperimentMetric(name="e", threshold=0.333, strategy=ExperimentMetric.CONSTRAINT),
        ExperimentMetric(name="c", strategy=ExperimentMetric.STORE),
        ExperimentMetric(name="h", threshold=0.444, strategy=ExperimentMetric.CONSTRAINT),
        ExperimentMetric(name="z"),
      ],
    )
    meta.observation_budget = numpy.random.randint(50, 200)
    meta.num_solutions = numpy.random.randint(2, 10)

    one_opt_three_constraint_experiment = Experiment(experiment_meta=meta)
    metrics_info, points_sampled = self.get_metrics_info_and_points_sampled_for_search_next_points(
      services,
      one_opt_three_constraint_experiment,
    )

    expected_threshold = numpy.quantile(
      points_sampled.values[:, 5],
      MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD,
    )
    expected_metrics_info = MetricsInfo(
      observation_budget=meta.observation_budget,
      objectives=["maximize", "maximize", "maximize", "maximize", "maximize", "maximize"],
      constraint_metrics_index=[2, 3, 4, 5],
      user_specified_thresholds=[None, None, 0.222, 0.333, 0.444, expected_threshold],
      optimized_metrics_index=[],
      requires_pareto_frontier_optimization=False,
    )
    assert expected_metrics_info == metrics_info
    assert not metrics_info.has_optimization_metrics
    assert metrics_info.has_constraint_metrics
    assert not metrics_info.has_optimized_metric_thresholds
