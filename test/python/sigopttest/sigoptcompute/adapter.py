# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest

from zigopt.experiment.model import Experiment
from zigopt.optimize.sources.base import OptimizationSource
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.sigoptcompute.adapter import SCAdapter

from libsigopt.aux.adapter_info_containers import DomainInfo
from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD,
  ParameterPriorNames,
)
from sigopttest.base.utils import partial_opt_args
from sigopttest.optimize.sources.base_test import UnitTestBase


class AdapterTests(UnitTestBase):
  @pytest.fixture
  def experiment(self):
    experiment_meta = ExperimentMeta(
      all_parameters_unsorted=[
        ExperimentParameter(
          name="double",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=-1, maximum=1),
        ),
        ExperimentParameter(
          name="double_log",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=1e-5, maximum=1),
          transformation=ExperimentParameter.TRANSFORMATION_LOG,
        ),
        ExperimentParameter(name="int", param_type=PARAMETER_INT, bounds=Bounds(minimum=-14, maximum=12)),
        ExperimentParameter(
          name="cat",
          param_type=PARAMETER_CATEGORICAL,
          all_categorical_values=[
            ExperimentCategoricalValue(name="c0_0", enum_index=0),
            ExperimentCategoricalValue(name="c0_1", enum_index=1, deleted=True),
            ExperimentCategoricalValue(name="c0_2", enum_index=2),
          ],
        ),
      ],
      observation_budget=100,
      parallel_bandwidth=4,
      metrics=[
        ExperimentMetric(name="m0"),
      ],
    )
    return Experiment(
      experiment_meta=experiment_meta,
      id=123,
      name="test experiment",
    )

  @pytest.fixture
  def experiment_with_parameter_priors(self):
    experiment_meta = ExperimentMeta(
      all_parameters_unsorted=[
        ExperimentParameter(
          name="parameter_normal",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=-5, maximum=5),
          prior=Prior(prior_type=Prior.NORMAL, normal_prior=NormalPrior(mean=1, scale=1.1)),
        ),
        ExperimentParameter(
          name="parameter_no_prior_double",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=-1, maximum=0),
        ),
        ExperimentParameter(
          name="parameter_no_prior_int",
          param_type=PARAMETER_INT,
          bounds=Bounds(minimum=1, maximum=10),
        ),
        ExperimentParameter(
          name="parameter_no_prior_cat",
          param_type=PARAMETER_CATEGORICAL,
          all_categorical_values=[
            ExperimentCategoricalValue(name="c0", enum_index=0),
            ExperimentCategoricalValue(name="c1", enum_index=1),
          ],
        ),
        ExperimentParameter(
          name="parameter_beta",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=0, maximum=1),
          prior=Prior(prior_type=Prior.BETA, beta_prior=BetaPrior(shape_a=1, shape_b=1.2)),
        ),
      ],
      observation_budget=100,
      parallel_bandwidth=4,
      metrics=[
        ExperimentMetric(name="m0"),
      ],
    )
    return Experiment(
      experiment_meta=experiment_meta,
      id=123,
      name="test experiment",
    )

  @pytest.fixture
  def multisolution_experiment(self):
    experiment_meta = ExperimentMeta(
      all_parameters_unsorted=[
        ExperimentParameter(
          name="double",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=-1, maximum=1),
        ),
        ExperimentParameter(
          name="double_log",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=1e-5, maximum=1),
          transformation=ExperimentParameter.TRANSFORMATION_LOG,
        ),
        ExperimentParameter(name="int", param_type=PARAMETER_INT, bounds=Bounds(minimum=-14, maximum=12)),
        ExperimentParameter(
          name="cat",
          param_type=PARAMETER_CATEGORICAL,
          all_categorical_values=[
            ExperimentCategoricalValue(name="c0_0", enum_index=0),
            ExperimentCategoricalValue(name="c0_1", enum_index=1),
          ],
        ),
      ],
      observation_budget=100,
      parallel_bandwidth=4,
      num_solutions=5,
      metrics=[
        ExperimentMetric(name="m1"),
        ExperimentMetric(name="m0", strategy=ExperimentMetric.CONSTRAINT, threshold=0.100),
      ],
    )
    return Experiment(
      experiment_meta=experiment_meta,
      id=123,
      name="test experiment",
    )

  @pytest.fixture
  def search_experiment(self):
    search_experiment_meta = ExperimentMeta(
      all_parameters_unsorted=[
        ExperimentParameter(
          name="double",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=-1, maximum=1),
        ),
        ExperimentParameter(
          name="double_log",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=1e-5, maximum=1),
          transformation=ExperimentParameter.TRANSFORMATION_LOG,
        ),
        ExperimentParameter(name="int", param_type=PARAMETER_INT, bounds=Bounds(minimum=-14, maximum=12)),
        ExperimentParameter(
          name="cat",
          param_type=PARAMETER_CATEGORICAL,
          all_categorical_values=[
            ExperimentCategoricalValue(name="c0_0", enum_index=0),
            ExperimentCategoricalValue(name="c0_1", enum_index=1),
          ],
        ),
      ],
      observation_budget=100,
      parallel_bandwidth=4,
      metrics=[ExperimentMetric(name="m0", threshold=1.7, objective=MINIMIZE, strategy=ExperimentMetric.CONSTRAINT)],
    )
    return Experiment(
      experiment_meta=search_experiment_meta,
      id=123,
      name="test search experiment",
    )


class TestAdapter(AdapterTests):
  def test_generate_domain_info(self, experiment):
    domain_info = SCAdapter.generate_domain_info(experiment)
    expected_domain_info = DomainInfo(
      constraint_list=[],
      domain_components=[
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2], "name": "cat"},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-1.0, 1.0], "name": "double"},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-5.0, 0.0], "name": "double_log"},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-14.0, 12.0], "name": "int"},
      ],
      force_hitandrun_sampling=False,
      priors=None,
    )
    assert domain_info == expected_domain_info
    assert domain_info.dim == 4

  def test_generate_domain_info_only_active_categoricals(self, experiment):
    domain_info = SCAdapter.generate_domain_info(experiment, only_active_categorical_values=True)
    expected_domain_info = DomainInfo(
      constraint_list=[],
      domain_components=[
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2], "name": "cat"},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-1.0, 1.0], "name": "double"},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-5.0, 0.0], "name": "double_log"},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-14.0, 12.0], "name": "int"},
      ],
      force_hitandrun_sampling=False,
      priors=None,
    )
    assert domain_info == expected_domain_info
    assert domain_info.dim == 4

  def test_generate_domain_info_priors(self, experiment_with_parameter_priors):
    domain_info = SCAdapter.generate_domain_info(experiment_with_parameter_priors)
    expected_domain_info = DomainInfo(
      constraint_list=[],
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0.0, 1.0], "name": "parameter_beta"},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1], "name": "parameter_no_prior_cat"},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-1.0, 0.0], "name": "parameter_no_prior_double"},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [1.0, 10.0], "name": "parameter_no_prior_int"},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-5.0, 5.0], "name": "parameter_normal"},
      ],
      force_hitandrun_sampling=False,
      priors=[
        {"name": ParameterPriorNames.BETA, "params": {"shape_a": 1, "shape_b": 1.2}},
        {"name": None, "params": None},
        {"name": None, "params": None},
        {"name": None, "params": None},
        {"name": ParameterPriorNames.NORMAL, "params": {"mean": 1, "scale": 1.1}},
      ],
    )
    assert domain_info == expected_domain_info
    assert domain_info.dim == 5

  def test_make_suggestion_data(self, services, experiment):
    suggested_points = [
      [0, -0.9, -4.0, 2],
      [1, -0.5, -3, -3],
      [0, 0.2, -0.1, 4],
    ]
    expected_assignments = [
      {"cat": 0.0, DOUBLE_EXPERIMENT_PARAMETER_NAME: -0.9, "double_log": 1e-4, INT_EXPERIMENT_PARAMETER_NAME: 2},
      {"cat": 1.0, DOUBLE_EXPERIMENT_PARAMETER_NAME: -0.5, "double_log": 1e-3, INT_EXPERIMENT_PARAMETER_NAME: -3},
      {"cat": 0.0, DOUBLE_EXPERIMENT_PARAMETER_NAME: 0.2, "double_log": 10**-0.1, INT_EXPERIMENT_PARAMETER_NAME: 4},
    ]
    sc_adapter = SCAdapter(services)
    # pylint: disable=protected-access
    suggestions = sc_adapter._make_suggestion_datas(experiment, suggested_points)
    # pylint: enable=protected-access
    assert len(suggestions) == 3
    for suggestion, expected in zip(suggestions, expected_assignments):
      values_dict = suggestion.get_assignments(experiment)
      assert values_dict == expected

  def test_make_points_sampled(self, services, experiment):
    suggestions = self.sample_suggestions(services, experiment, 7)
    observations = self.form_random_observations_from_suggestions(experiment, suggestions)
    # pylint: disable=protected-access
    points_sampled_dict = SCAdapter._make_points_sampled(experiment, observations, 7)
    for point in points_sampled_dict.points:
      assert point[0] in [0, 2]
      assert -1 <= point[1] <= 1
      assert -5 <= point[2] <= 0
      assert point[3] in range(-14, 13)

    with pytest.raises(AssertionError):
      points_sampled_dict = SCAdapter._make_points_sampled(experiment, [], 7)
    # pylint: enable=protected-access

  def test_make_points_being_sampled(self, services, experiment):
    suggestions = self.sample_suggestions(services, experiment, 7)
    opt_args = partial_opt_args(open_suggestions=suggestions)
    open_suggestions = OptimizationSource.extract_open_suggestion_datas(opt_args)
    # pylint: disable=protected-access
    points_being_sampled_dict = SCAdapter._make_points_being_sampled(experiment, open_suggestions)
    # pylint: enable=protected-access
    for point in points_being_sampled_dict.points:
      assert point[0] in [0, 2]
      assert -1 <= point[1] <= 1
      assert -5 <= point[2] <= 0
      assert point[3] in range(-14, 13)

  def test_form_metrics_info(self, experiment):
    metrics_info = SCAdapter.form_metrics_info(experiment)
    assert not metrics_info.requires_pareto_frontier_optimization
    assert metrics_info.observation_budget == 100
    assert metrics_info.user_specified_thresholds == [None]
    assert not metrics_info.has_optimized_metric_thresholds
    assert not metrics_info.has_constraint_metrics
    assert metrics_info.objectives == ["maximize"]
    assert metrics_info.optimized_metrics_index == [0]
    assert not metrics_info.constraint_metrics_index
    assert metrics_info.has_optimization_metrics

  def test_form_metrics_info_search(self, search_experiment):
    metrics_info = SCAdapter.form_metrics_info(search_experiment)
    assert not metrics_info.requires_pareto_frontier_optimization
    assert metrics_info.observation_budget == 100
    assert metrics_info.user_specified_thresholds == [1.7]
    assert not metrics_info.has_optimized_metric_thresholds
    assert metrics_info.has_constraint_metrics
    assert metrics_info.objectives == ["minimize"]
    assert not metrics_info.optimized_metrics_index
    assert metrics_info.constraint_metrics_index == [0]
    assert not metrics_info.has_optimization_metrics


class TestFormMetricsInfoForSearchNextPoints(AdapterTests):
  def get_points_sampled(self, services, experiment, num_observations, observation_values=None):
    suggestions = self.sample_suggestions(services, experiment, num_observations)
    observations = self.form_random_observations_from_suggestions(experiment, suggestions, observation_values)
    # pylint: disable=protected-access
    points_sampled = SCAdapter._make_points_sampled(experiment, observations, num_observations)
    # pylint: enable=protected-access
    return points_sampled

  @pytest.mark.parametrize("objective, expected_threshold", [["maximize", 4], ["minimize", 2]])
  def test_compute_multisolution_threshold(self, experiment, services, objective, expected_threshold):
    quantile_for_max = 0.75
    observation_values = [1, 2, 3, 4, 5]
    num_observations = len(observation_values)
    optimized_index = 0

    points_sampled = self.get_points_sampled(services, experiment, num_observations, observation_values)

    threshold = SCAdapter.compute_multisolution_threshold(
      [objective],
      points_sampled,
      optimized_index,
      quantile_for_max,
    )
    assert threshold == expected_threshold

  @pytest.mark.parametrize("objective, exp_threshold", [["maximize", 4], ["minimize", 2]])
  def test_compute_multisolution_threshold_with_failures(self, experiment, services, objective, exp_threshold):
    quantile_for_max = 0.75
    observation_values = [1, numpy.nan, 2, 3, 4, 5, numpy.nan]
    failures = [False, True, False, False, False, False, True]
    assert len(observation_values) == len(failures)

    num_observations = len(observation_values)
    optimized_index = 0

    points_sampled = self.get_points_sampled(services, experiment, num_observations, observation_values)
    points_sampled.failures = numpy.array(failures)

    threshold = SCAdapter.compute_multisolution_threshold(
      [objective],
      points_sampled,
      optimized_index,
      quantile_for_max,
    )
    assert threshold == exp_threshold

    # test if all failures raise an error
    points_sampled.failures = numpy.array([True] * len(observation_values))
    with pytest.raises(AssertionError):
      SCAdapter.compute_multisolution_threshold(
        "maximize",
        points_sampled,
        optimized_index,
        quantile_for_max,
      )

  def test_form_metrics_info_search_experiment(self, services, search_experiment):
    num_observations = 3
    points_sampled = self.get_points_sampled(services, search_experiment, num_observations)
    metrics_info = SCAdapter.form_metrics_info(search_experiment)
    mi_for_search = SCAdapter.form_metrics_info_for_search_next_point(search_experiment, points_sampled)
    assert mi_for_search == metrics_info

  def test_form_metrics_info_multisolution_experiment(self, services, multisolution_experiment):
    metrics_info = SCAdapter.form_metrics_info(multisolution_experiment)
    num_observations = 7
    points_sampled = self.get_points_sampled(services, multisolution_experiment, num_observations)
    expected_threshold = numpy.quantile(
      points_sampled.values[:, 1],
      MULTISOLUTION_QUANTILE_FOR_SEARCH_THRESHOLD,
    )
    mi_for_search = SCAdapter.form_metrics_info_for_search_next_point(multisolution_experiment, points_sampled)
    assert mi_for_search != metrics_info
    assert mi_for_search.user_specified_thresholds == [0.100, expected_threshold]
    assert not mi_for_search.optimized_metrics_index
    assert mi_for_search.constraint_metrics_index == [0, 1]
    assert not mi_for_search.has_optimized_metric_thresholds
    assert mi_for_search.has_constraint_metrics
