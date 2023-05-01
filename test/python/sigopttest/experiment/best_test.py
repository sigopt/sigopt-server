# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import random

import pytest
from mock import Mock

from zigopt.experiment.best import ExperimentBestObservationService
from zigopt.experiment.util import get_experiment_default_metric_name

from libsigopt.aux.constant import MULTISOLUTION_TOP_OBSERVATIONS_FRACTION
from libsigopt.aux.errors import SigoptComputeError


class TestExperimentBestObservationService:
  def create_mock_from_list(self, input_list):
    if input_list:
      return [
        Mock(
          id=i,
          data=value,
          value=value,
          metric_value=Mock(return_value=value),
          metric_value_var=Mock(return_value=value),
        )
        for i, value in enumerate(input_list)
      ]
    return None

  @pytest.mark.parametrize(
    "var_list",
    [
      [1e-3],
      [None, 0.5, None],
      [None, None, None, 1e-8],
    ],
  )
  def test_single_metric_best(self, var_list):
    services = Mock()
    experiment = Mock(optimized_metrics=[Mock(name="")], is_search=False)
    observations = self.create_mock_from_list(var_list)

    services.observation_service = Mock()
    services.observation_service.valid_observations = Mock(return_value=observations)

    experiment_best_observation_service = ExperimentBestObservationService(services)
    experiment_best_observation_service.best_from_valid_observations = Mock(return_value=1)  # type: ignore

    best = experiment_best_observation_service.single_metric_best(experiment, observations)
    assert experiment_best_observation_service.best_from_valid_observations.called  # type: ignore
    assert best == 1

  @pytest.mark.parametrize("var_list", [[], [None, 0], [None, None, None], [0.0, 0.00000], [0.0, None]])
  def test_single_metric_best_when_var_was_not_reported(self, var_list):
    services = Mock()
    experiment = Mock(optimized_metrics=[Mock(name="")], is_search=False)
    observations = self.create_mock_from_list(var_list) if var_list else var_list

    services.observation_service = Mock()
    services.observation_service.valid_observations = Mock(return_value=observations)

    experiment_best_observation_service = ExperimentBestObservationService(services)
    experiment_best_observation_service.best_from_valid_observations = Mock(return_value=1)  # type: ignore
    best = experiment_best_observation_service.single_metric_best(experiment, observations)
    assert experiment_best_observation_service.best_from_valid_observations.called  # type: ignore
    assert best == 1

  @pytest.mark.parametrize("return_value", [1, None])
  def test_get_best_observations_single_metric(self, return_value):
    services = Mock()
    experiment = Mock(
      num_solutions=1,
      optimized_metrics=[Mock(name="")],
      requires_pareto_frontier_optimization=False,
      is_search=False,
    )
    observations = Mock()
    experiment_best_observation_service = ExperimentBestObservationService(services)
    experiment_best_observation_service.single_metric_best = Mock(return_value=return_value)  # type: ignore
    best = experiment_best_observation_service.get_best_observations(experiment, observations)
    assert experiment_best_observation_service.single_metric_best.called  # type: ignore
    if return_value is None:
      assert best == []
    else:
      assert best == [return_value]

  @pytest.mark.parametrize(
    "values, sorted_values",
    [
      ([1, 3, 5], [5, 3, 1]),
      ([-1, 2, 0], [2, 0, -1]),
      ([-5, float("nan"), -2], [-2, -5]),
      ([None, 3, 4, None, 2], [4, 3, 2]),
    ],
  )
  def test_get_best_observations_multimetric(self, values, sorted_values):
    services = Mock()
    first_metric = Mock()
    first_metric.name = "a"
    experiment = Mock(
      optimized_metrics=[first_metric, Mock(name="b")],
      requires_pareto_frontier_optimization=True,
      is_search=False,
    )
    observations = [Mock(value_for_maximization=Mock(return_value=val)) for val in values]
    best_observation_service = ExperimentBestObservationService(services)
    best_observation_service.pareto_frontier = Mock(return_value=observations)  # type: ignore
    sorted_observations = best_observation_service.get_best_observations(experiment, observations)
    assert best_observation_service.pareto_frontier.called  # type: ignore
    default_metric_name = get_experiment_default_metric_name(experiment)
    assert default_metric_name == "a"
    for o, val in zip(sorted_observations, sorted_values):
      assert o.value_for_maximization() == val

  @pytest.mark.parametrize(
    "values, expected_sorted_values, within_metric_thresholds",
    [
      ([1, 3, 5], [5, 3, 1], [True, True, True]),
      ([1, 3, 5], [3, 1], [True, True, False]),
      ([-1, 2, 0], [0, -1], [True, False, True]),
      ([-5, float("nan"), -2], [-2, -5], [True, True, True]),
      ([-5, -3, -2], [], [False, False, False]),
      ([None, 3, 4, None, 2], [4, 2], [True, False, True, True, True]),
    ],
  )
  def test_get_best_observations_search(self, values, expected_sorted_values, within_metric_thresholds):
    services = Mock()
    first_metric = Mock()
    first_metric.name = "a"
    experiment = Mock(
      constraint_metrics=[first_metric, Mock(name="b")],
      requires_pareto_frontier_optimization=False,
      is_search=True,
    )
    observations = [
      Mock(
        value_for_maximization=Mock(return_value=val),
        within_metric_thresholds=Mock(return_value=within),
      )
      for val, within in zip(values, within_metric_thresholds)
    ]
    best_observation_service = ExperimentBestObservationService(services)
    sorted_observations = best_observation_service.get_best_observations(experiment, observations)
    default_metric_name = get_experiment_default_metric_name(experiment)
    assert default_metric_name == "a"
    for o, val in zip(sorted_observations, expected_sorted_values):
      assert o.value_for_maximization() == val

  @pytest.mark.parametrize("num_observations", [1, 12, 25, 50, 100])
  @pytest.mark.parametrize("num_solutions", [2, 3, 50, 99])
  def test_get_best_observations_multisolution_no_failures(
    self,
    num_observations,
    num_solutions,
  ):
    values = [random.uniform(-10, 30) for _ in range(num_observations)]
    best_values = sorted(values, reverse=True)
    best_values = best_values[:num_solutions]

    services = Mock()
    best_assignments_mock_indices = list(range(min(num_observations, num_solutions)))
    services.sc_adapter.multisolution_best_assignments = Mock(return_value=best_assignments_mock_indices)
    services.exception_logger.soft_exception = Mock()

    first_metric = Mock()
    first_metric.name = "a"
    experiment = Mock(
      optimized_metrics=[first_metric, Mock(name="b")],
      requires_pareto_frontier_optimization=False,
      is_search=False,
      num_solutions=num_solutions,
    )
    observations = [
      Mock(
        value_for_maximization=Mock(return_value=val),
        within_metric_thresholds=Mock(return_value=True),
      )
      for val in values
    ]

    best_observation_service = ExperimentBestObservationService(services)
    best_observations = best_observation_service.get_best_observations(experiment, observations)

    if round(num_observations * MULTISOLUTION_TOP_OBSERVATIONS_FRACTION) > num_solutions:
      services.sc_adapter.multisolution_best_assignments.assert_called_once()
    else:
      services.sc_adapter.multisolution_best_assignments.assert_not_called()
    services.exception_logger.soft_exception.assert_not_called()  # type: ignore

    default_metric_name = get_experiment_default_metric_name(experiment)
    assert default_metric_name == "a"
    assert len(best_observations) == len(best_values)
    for o, val in zip(best_observations, best_values):
      assert o.value_for_maximization() == val

  def test_multisolution_best_assignments_soft_exception(self):
    num_observations = 30
    num_solutions = 3
    values = list(range(num_observations))
    best_values = sorted(values, reverse=True)
    best_values = best_values[:num_solutions]

    services = Mock()
    services.sc_adapter.multisolution_best_assignments = Mock(side_effect=SigoptComputeError("SigoptComputeError Test"))
    services.exception_logger.soft_exception = Mock()

    first_metric = Mock()
    first_metric.name = "a"
    experiment = Mock(
      optimized_metrics=[first_metric, Mock(name="b")],
      requires_pareto_frontier_optimization=False,
      is_search=False,
      num_solutions=num_solutions,
    )
    observations = [
      Mock(
        value_for_maximization=Mock(return_value=val),
        within_metric_thresholds=Mock(return_value=True),
      )
      for val in values
    ]
    best_observation_service = ExperimentBestObservationService(services)

    best_observations = best_observation_service.get_best_observations(experiment, observations)

    services.sc_adapter.multisolution_best_assignments.assert_called_once()
    services.exception_logger.soft_exception.assert_called_once()  # type: ignore

    default_metric_name = get_experiment_default_metric_name(experiment)
    assert default_metric_name == "a"
    assert len(best_observations) == len(best_values) == num_solutions
    for o, val in zip(best_observations, best_values):
      assert o.value_for_maximization() == val

  @pytest.mark.parametrize("num_observations", [2, 5, 30, 50])
  def test_multiple_solutions_best(self, num_observations):
    # pylint: disable=too-many-locals
    observation_values = list(range(num_observations))
    num_solutions = 2
    num_top_observations = max(round(num_observations * MULTISOLUTION_TOP_OBSERVATIONS_FRACTION), num_solutions)
    top_observations = list(range(num_top_observations))
    best_indices = [2, 5]

    if num_top_observations > num_solutions:
      best_values = [top_observations[i] for i in best_indices]
    else:
      best_values = top_observations[:num_solutions]

    first_metric = Mock()
    first_metric.name = "a"
    experiment = Mock(
      optimized_metrics=[first_metric, Mock(name="b")],
      requires_pareto_frontier_optimization=False,
      is_search=False,
      num_solutions=num_solutions,
    )
    observations = [
      Mock(
        value_for_maximization=Mock(return_value=val),
        within_metric_thresholds=Mock(return_value=True),
      )
      for val in observation_values
    ]
    services = Mock()
    services.observation_service = Mock()
    services.sc_adapter.multisolution_best_assignments = Mock(return_value=best_indices)
    services.exception_logger.soft_exception = Mock()

    experiment_best_observation_service = ExperimentBestObservationService(services)
    experiment_best_observation_service.multi_metric_best = Mock(return_value=observations)  # type: ignore

    best_observations = experiment_best_observation_service.multiple_solutions_best(
      experiment,
      observations,
    )

    if num_top_observations > num_solutions:
      services.sc_adapter.multisolution_best_assignments.assert_called_once()
    services.exception_logger.soft_exception.assert_not_called()  # type: ignore
    default_metric_name = get_experiment_default_metric_name(experiment)
    assert default_metric_name == "a"
    assert len(best_observations) == len(best_values) == num_solutions
    for o, val in zip(best_observations, best_values):
      assert o.value_for_maximization() == val
