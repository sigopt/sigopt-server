# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock, patch

from zigopt.experiment.model import Experiment
from zigopt.handlers.experiments.create import BaseExperimentsCreateHandler
from zigopt.optimize.optimizer import OptimizerService
from zigopt.optimize.sources.search import SearchOptimizationSource
from zigopt.optimize.sources.spe import SPEOptimizationSource


class TestSearchExperimentProgress:
  @pytest.fixture(
    params=[
      "multisolution",
      "search",
    ]
  )
  def search_experiment(self, request):
    experiment = Mock()
    if request.param == "search":
      experiment.is_search = True
    elif request.param == "multisolution":
      experiment.is_search = False
      experiment.num_solutions = 2
    experiment.all_parameters = [Mock(is_categorical=False)] * 5
    experiment.conditionals = []
    experiment.constraints = []
    return experiment

  @pytest.fixture
  def not_search_experiment(self):
    experiment = Mock()
    experiment.is_search = False
    experiment.num_solutions = 1
    experiment.conditionals = True
    return experiment

  def test_hyper_opt_dimension(self):
    json_dict = {
      "name": "test",
      "parameters": [{"name": f"x{k}", "type": "double", "bounds": {"min": 0, "max": 1}} for k in range(5)],
    }
    experiment_meta = BaseExperimentsCreateHandler.make_experiment_meta_from_json(json_dict, "offline", False)
    experiment = Experiment(experiment_meta=experiment_meta)
    source = SearchOptimizationSource(None, experiment)
    assert source.hyper_opt_dimension == 5

    json_dict = {
      "name": "test",
      "parameters": [{"name": f"x{k}", "type": "double", "bounds": {"min": 0, "max": 1}} for k in range(4)]
      + [{"name": f"c{k}", "type": "categorical", "categorical_values": ["a", "b"]} for k in range(3)],
    }
    experiment_meta = BaseExperimentsCreateHandler.make_experiment_meta_from_json(json_dict, "offline", False)
    experiment = Experiment(experiment_meta=experiment_meta)
    source = SearchOptimizationSource(None, experiment)
    assert source.hyper_opt_dimension == 4 + 6

    json_dict = {
      "name": "test",
      "parameters": [{"name": f"x{k}", "type": "int", "bounds": {"min": 0, "max": 1}} for k in range(4)]
      + [{"name": f"c{k}", "type": "categorical", "categorical_values": ["a", "b", "c"]} for k in range(5)]
      + [{"name": f"cc{k}", "type": "categorical", "categorical_values": ["b", "c"]} for k in range(6)],
    }
    experiment_meta = BaseExperimentsCreateHandler.make_experiment_meta_from_json(json_dict, "offline", False)
    experiment = Experiment(experiment_meta=experiment_meta)
    source = SearchOptimizationSource(None, experiment)
    assert source.hyper_opt_dimension == 4 + 5 * 3 + 6 * 2

  def test_should_have_task_length_false(self):
    json_dict = {
      "name": "test",
      "parameters": [{"name": f"x{k}", "type": "double", "bounds": {"min": 0, "max": 1}} for k in range(5)],
    }
    experiment_meta = BaseExperimentsCreateHandler.make_experiment_meta_from_json(json_dict, "offline", False)
    experiment: Experiment | None = Experiment(experiment_meta=experiment_meta)
    source = SearchOptimizationSource(None, experiment)
    assert source.should_have_task_length() is False

    experiment = None
    source = SearchOptimizationSource(None, experiment)
    assert source.should_have_task_length() is False

  def test_optimize_service_returns_search_source(self, search_experiment):
    service = Mock(config_broker={})
    optimizer = OptimizerService(service)
    source = optimizer.get_inferred_optimization_source(search_experiment, 5)
    assert isinstance(source, SearchOptimizationSource)

  def test_optimize_service_force_spe_source(self, search_experiment):
    service = Mock(config_broker={"model.force_spe": True})
    optimizer = OptimizerService(service)
    source = optimizer.get_inferred_optimization_source(search_experiment, 5)
    assert isinstance(source, SPEOptimizationSource)

  def test_optimize_service_does_not_return_search_source(self, not_search_experiment):
    service = Mock()
    with patch("zigopt.optimize.optimizer.ConditionalOptimizationSource"):
      optimizer = OptimizerService(service)
      source = optimizer.get_inferred_optimization_source(not_search_experiment, None)
      assert not isinstance(source, SearchOptimizationSource)
