# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from mock import Mock

from zigopt.experiment.model import Experiment, ExperimentParameterProxy
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  ExperimentMeta,
  ExperimentParameter,
)
from zigopt.protobuf.lib import copy_protobuf
from zigopt.suggestion.sampler.xgb_sampler import XGBSampler


def int_parameter(name, minimum, maximum):
  parameter = ExperimentParameter()
  parameter.name = name
  parameter.param_type = PARAMETER_INT
  parameter.bounds.minimum = minimum
  parameter.bounds.maximum = maximum
  return ExperimentParameterProxy(parameter)


def double_parameter(name, minimum, maximum):
  parameter = ExperimentParameter()
  parameter.name = name
  parameter.param_type = PARAMETER_DOUBLE
  parameter.bounds.minimum = minimum
  parameter.bounds.maximum = maximum
  return ExperimentParameterProxy(parameter)


def fake_experiment(all_parameters):
  experiment = Experiment(
    experiment_meta=ExperimentMeta(all_parameters_unsorted=[copy_protobuf(param) for param in all_parameters])
  )
  return experiment


class TestXGBSamplerFunctionality:
  services = Mock()
  optimization_args = Mock()

  def test_check_all_priors(self):
    params = [
      double_parameter("eta", 0.0001, 1),
    ]
    experiment = fake_experiment(params)
    xgb_sampler = XGBSampler(self.services, experiment, self.optimization_args)
    assert "eta" in xgb_sampler.priors
    assert "gamma" in xgb_sampler.priors
    assert "max_depth" in xgb_sampler.priors
    assert "min_child_weight" in xgb_sampler.priors
    assert "max_delta_step" in xgb_sampler.priors

  def test_cdf_sufficient_mass(self):
    params = [
      double_parameter("eta", 0.0001, 1),
      double_parameter("gamma", 1, 5),
      int_parameter("max_depth", 1, 20),
      double_parameter("min_child_weight", 1, 5),
      double_parameter("max_delta_step", 1, 5),
    ]
    experiment = fake_experiment(params)
    xgb_sampler = XGBSampler(self.services, experiment, self.optimization_args)
    assert "eta" in xgb_sampler.active_priors
    assert "gamma" in xgb_sampler.active_priors
    assert "max_depth" in xgb_sampler.active_priors
    assert "min_child_weight" in xgb_sampler.active_priors
    assert "max_delta_step" in xgb_sampler.active_priors

  def test_cdf_insufficient_mass(self):
    params = [
      double_parameter("eta", 0.999, 1),
      double_parameter("gamma", 4.999, 5),
      int_parameter("max_depth", 31, 32),
      double_parameter("min_child_weight", 4.999, 5),
      double_parameter("max_delta_step", 1.999, 5),
    ]
    experiment = fake_experiment(params)
    xgb_sampler = XGBSampler(self.services, experiment, self.optimization_args)
    assert "eta" not in xgb_sampler.active_priors
    assert "gamma" not in xgb_sampler.active_priors
    assert "max_depth" not in xgb_sampler.active_priors
    assert "min_child_weight" not in xgb_sampler.active_priors
    assert "max_delta_step" not in xgb_sampler.active_priors
    sample = xgb_sampler.generate_random_suggestion_datas(count=1)[0]
    for param in params:
      assert param.valid_assignment(sample.get_assignment(param))

  def test_cdf_out_of_bounds_right(self):
    params = [
      double_parameter("eta", 100, 101),
      double_parameter("gamma", 100, 101),
      int_parameter("max_depth", 100, 101),
      double_parameter("min_child_weight", 100, 101),
      double_parameter("max_delta_step", 100, 101),
    ]
    experiment = fake_experiment(params)
    xgb_sampler = XGBSampler(self.services, experiment, self.optimization_args)
    assert "eta" not in xgb_sampler.active_priors
    assert "gamma" not in xgb_sampler.active_priors
    assert "max_depth" not in xgb_sampler.active_priors
    assert "min_child_weight" not in xgb_sampler.active_priors
    assert "max_delta_step" not in xgb_sampler.active_priors

  def test_cdf_out_of_bounds_left(self):
    params = [
      double_parameter("eta", -100, -101),
      double_parameter("gamma", -100, -101),
      int_parameter("max_depth", -100, -101),
      double_parameter("min_child_weight", -100, -101),
      double_parameter("max_delta_step", -100, -101),
    ]
    experiment = fake_experiment(params)
    xgb_sampler = XGBSampler(self.services, experiment, self.optimization_args)
    assert "eta" not in xgb_sampler.active_priors
    assert "gamma" not in xgb_sampler.active_priors
    assert "max_depth" not in xgb_sampler.active_priors
    assert "min_child_weight" not in xgb_sampler.active_priors
    assert "max_delta_step" not in xgb_sampler.active_priors

  def test_log_prior_bounds(self):
    params = [
      double_parameter("eta", 0, 1),
    ]
    experiment = fake_experiment(params)
    xgb_sampler = XGBSampler(self.services, experiment, self.optimization_args)
    assert "eta" not in xgb_sampler.active_priors

    params = [
      double_parameter("eta", -1, 1),
    ]
    experiment = fake_experiment(params)
    xgb_sampler = XGBSampler(self.services, experiment, self.optimization_args)
    assert "eta" not in xgb_sampler.active_priors

    params = [
      double_parameter("eta", -1, 0),
    ]
    experiment = fake_experiment(params)
    xgb_sampler = XGBSampler(self.services, experiment, self.optimization_args)
    assert "eta" not in xgb_sampler.active_priors
