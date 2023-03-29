# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from mock import Mock

from zigopt.config.broker import ConfigBroker
from zigopt.experiment.model import Experiment
from zigopt.handlers.experiments.create import BaseExperimentsCreateHandler
from zigopt.optimize.sources.categorical import CategoricalOptimizationSource

from libsigopt.aux.constant import (
  DEFAULT_USE_SPE_AFTER_THIS_MANY_OBSERVATIONS,
  DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS,
)


class TestExperimentProgress(object):
  def test_hyper_opt_dimension(self):
    json_dict = {
      "name": "test",
      "parameters": [{"name": f"x{k}", "type": "double", "bounds": {"min": 0, "max": 1}} for k in range(5)],
    }
    experiment_meta = BaseExperimentsCreateHandler.make_experiment_meta_from_json(json_dict, "offline", False)
    experiment = Experiment(experiment_meta=experiment_meta)
    source = CategoricalOptimizationSource(None, experiment)
    assert source.hyper_opt_dimension == 5

    json_dict = {
      "name": "test",
      "parameters": [{"name": f"x{k}", "type": "double", "bounds": {"min": 0, "max": 1}} for k in range(4)]
      + [{"name": f"c{k}", "type": "categorical", "categorical_values": ["a", "b"]} for k in range(3)],
    }
    experiment_meta = BaseExperimentsCreateHandler.make_experiment_meta_from_json(json_dict, "offline", False)
    experiment = Experiment(experiment_meta=experiment_meta)
    source = CategoricalOptimizationSource(None, experiment)
    assert source.hyper_opt_dimension == 4 + 6

    json_dict = {
      "name": "test",
      "parameters": [{"name": f"x{k}", "type": "int", "bounds": {"min": 0, "max": 1}} for k in range(4)]
      + [{"name": f"c{k}", "type": "categorical", "categorical_values": ["a", "b", "c"]} for k in range(5)]
      + [{"name": f"cc{k}", "type": "categorical", "categorical_values": ["b", "c"]} for k in range(6)],
    }
    experiment_meta = BaseExperimentsCreateHandler.make_experiment_meta_from_json(json_dict, "offline", False)
    experiment = Experiment(experiment_meta=experiment_meta)
    source = CategoricalOptimizationSource(None, experiment)
    assert source.hyper_opt_dimension == 4 + 5 * 3 + 6 * 2

  def test_is_suitable_at_this_point(self):
    json_dict = {
      "name": "test",
      "parameters": [
        {"name": f"x{k}", "type": "double", "bounds": {"min": 0, "max": 1}}
        for k in range(DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS - 1)
      ],
    }
    experiment_meta = BaseExperimentsCreateHandler.make_experiment_meta_from_json(json_dict, "offline", False)
    experiment = Experiment(experiment_meta=experiment_meta)
    services = Mock()
    services.config_broker = ConfigBroker.from_configs([{}])
    source = CategoricalOptimizationSource(services, experiment)
    assert experiment.dimension <= DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS
    assert source.is_suitable_at_this_point(0)
    assert source.is_suitable_at_this_point(DEFAULT_USE_SPE_AFTER_THIS_MANY_OBSERVATIONS - 1)
    assert not source.is_suitable_at_this_point(DEFAULT_USE_SPE_AFTER_THIS_MANY_OBSERVATIONS)

    json_dict = {
      "name": "test",
      "parameters": [
        {"name": f"x{k}", "type": "double", "bounds": {"min": 0, "max": 1}}
        for k in range(DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS // 2)
      ]
      + [
        {"name": f"c{k}", "type": "categorical", "categorical_values": ["a", "b"]}
        for k in range(DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS // 2)
      ],
    }
    experiment_meta = BaseExperimentsCreateHandler.make_experiment_meta_from_json(json_dict, "offline", False)
    experiment = Experiment(experiment_meta=experiment_meta)
    source = CategoricalOptimizationSource(services, experiment)
    assert experiment.dimension <= DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS
    assert not source.is_suitable_at_this_point(0)
    assert not source.is_suitable_at_this_point(DEFAULT_USE_SPE_AFTER_THIS_MANY_OBSERVATIONS - 1)
    assert not source.is_suitable_at_this_point(DEFAULT_USE_SPE_AFTER_THIS_MANY_OBSERVATIONS)
