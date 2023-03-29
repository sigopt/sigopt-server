# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy

import numpy
import pytest
from mock import Mock

from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  QUANTIZED_EXPERIMENT_PARAMETER_NAME,
)
from libsigopt.compute.domain import CategoricalDomain
from libsigopt.compute.misc.constant import NONZERO_MEAN_CONSTANT_MEAN_TYPE, QUANTIZED_LENGTH_SCALE_LOWER_FACTOR
from libsigopt.compute.views.rest.gp_hyper_opt_multimetric import (
  DEFAULT_HYPER_OPT_OPTIMIZER_INFO,
  GpHyperOptMultimetricView,
  form_one_hot_hyperparameter_domain,
)
from testaux.numerical_test_case import NumericalTestCase
from testcompute.zigopt_input_utils import ZigoptSimulator


class TestCategoricalTools(NumericalTestCase):
  def assert_hyperparameter_dict_keys(self, hyperparameter_dict):
    assert set(hyperparameter_dict.keys()) == {"alpha", "length_scales", "tikhonov", "task_length"}

  def assert_length_scales_valid(self, length_scales, domain):
    assert len(length_scales) == domain.dim
    for domain_component, ls in zip(domain, length_scales):
      assert all(l > 0 for l in ls)
      if domain_component["var_type"] == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
        assert len(ls) == len(domain_component["elements"])
      else:
        assert len(ls) == 1

  def test_form_one_hot_hyperparameter_domain(self):
    domain = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3.3, 6.1]},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [1, 3, 5, 10]},
      ],
    )
    historical_data = Mock(points_sampled_value=[1, 2, 3, 4, 5, 6, 7])
    discrete_lower_limit = 0.234567

    hp_domain = form_one_hot_hyperparameter_domain(
      categorical_domain=domain,
      historical_data=historical_data,
      use_auto_noise=False,
      discrete_lower_limit=discrete_lower_limit,
      task_cost_populated=False,
      select_hyper_opt_in_log_domain=False,
    )
    assert hp_domain.dim == 9
    for db in hp_domain.domain_bounds[2:5]:
      assert db[0] == discrete_lower_limit
    assert hp_domain.domain_bounds[6][0] >= discrete_lower_limit
    assert hp_domain.domain_bounds[-1][0] == QUANTIZED_LENGTH_SCALE_LOWER_FACTOR * (5 - 3)

    hp_domain_log = form_one_hot_hyperparameter_domain(
      categorical_domain=domain,
      historical_data=historical_data,
      use_auto_noise=False,
      discrete_lower_limit=discrete_lower_limit,
      task_cost_populated=False,
      select_hyper_opt_in_log_domain=True,
    )
    assert hp_domain_log.dim == 9
    for db, db_log in zip(hp_domain.domain_bounds, hp_domain_log.domain_bounds):
      assert numpy.log(db[0]) == db_log[0]
      assert numpy.log(db[1]) == db_log[1]

    hp_domain_tikhonov = form_one_hot_hyperparameter_domain(
      categorical_domain=domain,
      historical_data=historical_data,
      use_auto_noise=True,
      discrete_lower_limit=discrete_lower_limit,
      task_cost_populated=False,
      select_hyper_opt_in_log_domain=False,
    )
    assert hp_domain_tikhonov.dim == 10
    for db, db_tik in zip(hp_domain.domain_bounds, hp_domain_tikhonov.domain_bounds[:-1]):
      assert db[0] == db_tik[0] and db[1] == db_tik[1]

    hp_domain_tikhonov_task = form_one_hot_hyperparameter_domain(
      categorical_domain=domain,
      historical_data=historical_data,
      use_auto_noise=True,
      discrete_lower_limit=discrete_lower_limit,
      task_cost_populated=True,
      select_hyper_opt_in_log_domain=False,
    )
    assert hp_domain_tikhonov_task.dim == 11
    for db, db_tt in zip(hp_domain.domain_bounds, hp_domain_tikhonov_task.domain_bounds[:-2]):
      assert db[0] == db_tt[0] and db[1] == db_tt[1]
    db_tik = hp_domain_tikhonov.domain_bounds[-1]
    db_tt = hp_domain_tikhonov_task.domain_bounds[-1]
    assert db_tik[0] == db_tt[0] and db_tik[1] == db_tt[1]

  def test_optimizer_info(self):
    zs = ZigoptSimulator(
      dim=5,
      num_sampled=29,
      num_optimized_metrics=1,
      num_to_sample=None,
      nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
      use_tikhonov=False,
      num_tasks=0,
    )

    view_input, _ = zs.form_gp_hyper_opt_categorical_inputs()
    view_object = GpHyperOptMultimetricView(view_input)
    assert view_object.optimizer_info == DEFAULT_HYPER_OPT_OPTIMIZER_INFO

  @pytest.mark.parametrize("dim", [2, 5])
  @pytest.mark.parametrize("num_sampled", [21, 37])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  def test_acceptable_responses_base(
    self,
    dim,
    num_sampled,
    nonzero_mean_type,
    num_optimized_metrics,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_to_sample=None,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=False,
      num_tasks=0,
    )
    view_input, domain = zs.form_gp_hyper_opt_categorical_inputs()
    response = GpHyperOptMultimetricView(view_input).call()
    hyperparameter_dicts = response["hyperparameter_dict"]
    assert len(hyperparameter_dicts) == num_optimized_metrics

    for hyperparameter_dict in hyperparameter_dicts:
      self.assert_hyperparameter_dict_keys(hyperparameter_dict)
      assert hyperparameter_dict["alpha"] > 0
      assert hyperparameter_dict["task_length"] is None
      assert hyperparameter_dict["tikhonov"] is None
      self.assert_length_scales_valid(hyperparameter_dict["length_scales"], domain)

  @pytest.mark.parametrize("num_optimized_metrics", [1])
  @pytest.mark.parametrize("num_constraint_metrics", [0, 2])
  @pytest.mark.parametrize("num_stored_metrics", [1])
  def test_metric_strategy_not_optimizing_stored_metrics(
    self,
    num_optimized_metrics,
    num_constraint_metrics,
    num_stored_metrics,
  ):
    num_metrics = num_optimized_metrics + num_constraint_metrics + num_stored_metrics
    zs = ZigoptSimulator(
      dim=2,
      num_sampled=23,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_stored_metrics=num_stored_metrics,
      num_to_sample=None,
      nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
      use_tikhonov=False,
      num_tasks=0,
    )
    view_input, domain = zs.form_gp_hyper_opt_categorical_inputs()
    old_hyperparameter_dict = deepcopy(view_input["model_info"].hyperparameters)
    optimized_metrics_index = view_input["metrics_info"].optimized_metrics_index
    constraint_metrics_index = view_input["metrics_info"].constraint_metrics_index

    response = GpHyperOptMultimetricView(view_input).call()
    hyperparameter_dicts = response["hyperparameter_dict"]

    assert len(hyperparameter_dicts) == num_metrics
    for i, hyperparameter_dict in enumerate(hyperparameter_dicts):
      if i not in numpy.append(optimized_metrics_index, constraint_metrics_index):
        assert hyperparameter_dict["alpha"] == old_hyperparameter_dict[i]["alpha"]
        assert hyperparameter_dict["task_length"] is None
        assert hyperparameter_dict["tikhonov"] is None
        self.assert_length_scales_valid(hyperparameter_dict["length_scales"], domain)
        for j, ls in enumerate(hyperparameter_dict["length_scales"]):
          assert ls == old_hyperparameter_dict[i]["length_scales"][j]

  @pytest.mark.parametrize("dim", [7])
  @pytest.mark.parametrize("num_sampled", [53])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  def test_acceptable_responses_tikhonov(
    self,
    dim,
    num_sampled,
    nonzero_mean_type,
    num_optimized_metrics,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_to_sample=None,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=True,
      num_tasks=0,
    )
    view_input, domain = zs.form_gp_hyper_opt_categorical_inputs()
    response = GpHyperOptMultimetricView(view_input).call()
    hyperparameter_dicts = response["hyperparameter_dict"]
    assert len(hyperparameter_dicts) == num_optimized_metrics

    for hyperparameter_dict in hyperparameter_dicts:
      self.assert_hyperparameter_dict_keys(hyperparameter_dict)
      assert hyperparameter_dict["alpha"] > 0
      assert hyperparameter_dict["task_length"] is None
      assert hyperparameter_dict["tikhonov"] > 0
      self.assert_length_scales_valid(hyperparameter_dict["length_scales"], domain)

  @pytest.mark.parametrize("dim", [5])
  @pytest.mark.parametrize("num_sampled", [38])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  def test_acceptable_responses_multitask(
    self,
    dim,
    num_sampled,
    nonzero_mean_type,
    num_optimized_metrics,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_to_sample=None,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=False,
      num_tasks=3,
    )
    view_input, domain = zs.form_gp_hyper_opt_categorical_inputs()
    response = GpHyperOptMultimetricView(view_input).call()
    hyperparameter_dicts = response["hyperparameter_dict"]
    assert len(hyperparameter_dicts) == num_optimized_metrics

    for hyperparameter_dict in hyperparameter_dicts:
      self.assert_hyperparameter_dict_keys(hyperparameter_dict)
      assert hyperparameter_dict["alpha"] > 0
      assert hyperparameter_dict["task_length"] > 0
      assert hyperparameter_dict["tikhonov"] is None
      self.assert_length_scales_valid(hyperparameter_dict["length_scales"], domain)

  @pytest.mark.parametrize("dim", [6])
  @pytest.mark.parametrize("num_sampled", [27])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("num_optimized_metrics", [0, 1])
  @pytest.mark.parametrize("num_constraint_metrics", [0, 1])
  @pytest.mark.parametrize("num_stored_metrics", [1])
  def test_acceptable_responses_no_optimized_metrics(
    self,
    dim,
    num_sampled,
    nonzero_mean_type,
    num_optimized_metrics,
    num_constraint_metrics,
    num_stored_metrics,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_stored_metrics=num_stored_metrics,
      num_to_sample=None,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=False,
      num_tasks=0,
    )
    num_metrics = num_optimized_metrics + num_constraint_metrics + num_stored_metrics
    view_input, domain = zs.form_gp_hyper_opt_categorical_inputs()
    old_hyperparameter_dict = deepcopy(view_input["model_info"].hyperparameters)
    optimized_metrics_index = view_input["metrics_info"].optimized_metrics_index
    constraint_metrics_index = view_input["metrics_info"].constraint_metrics_index
    if (num_optimized_metrics + num_constraint_metrics) > 0:
      response = GpHyperOptMultimetricView(view_input).call()
      hyperparameter_dicts = response["hyperparameter_dict"]
      assert len(hyperparameter_dicts) == num_metrics
      for i, hyperparameter_dict in enumerate(hyperparameter_dicts):
        if i in numpy.append(optimized_metrics_index, constraint_metrics_index):
          self.assert_hyperparameter_dict_keys(hyperparameter_dict)
          assert hyperparameter_dict["alpha"] > 0
          assert hyperparameter_dict["task_length"] is None
          assert hyperparameter_dict["tikhonov"] is None
          self.assert_length_scales_valid(hyperparameter_dict["length_scales"], domain)
        else:
          assert hyperparameter_dict["alpha"] == old_hyperparameter_dict[i]["alpha"]
          assert hyperparameter_dict["task_length"] is None
          assert hyperparameter_dict["tikhonov"] is None
          self.assert_length_scales_valid(hyperparameter_dict["length_scales"], domain)
          for j, ls in enumerate(hyperparameter_dict["length_scales"]):
            assert ls == old_hyperparameter_dict[i]["length_scales"][j]
    else:
      with pytest.raises(AssertionError):
        GpHyperOptMultimetricView(view_input).call()

  @pytest.mark.parametrize("num_optimized_metrics", [1])
  @pytest.mark.parametrize("num_constraint_metrics", [0, 1])
  def test_not_optimizing_same_point_sampled_values(
    self,
    num_optimized_metrics,
    num_constraint_metrics,
  ):
    num_metrics = num_optimized_metrics + num_constraint_metrics
    zs = ZigoptSimulator(
      dim=2,
      num_sampled=23,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_to_sample=None,
      nonzero_mean_type=NONZERO_MEAN_CONSTANT_MEAN_TYPE,
      use_tikhonov=False,
      num_tasks=0,
    )
    view_input, domain = zs.form_gp_hyper_opt_categorical_inputs()
    view_input["points_sampled"].values = 3.14 * numpy.ones_like(view_input["points_sampled"].values)
    old_hyperparameter_dict = deepcopy(view_input["model_info"].hyperparameters)

    response = GpHyperOptMultimetricView(view_input).call()
    hyperparameter_dicts = response["hyperparameter_dict"]

    assert len(hyperparameter_dicts) == num_metrics
    for i, hyperparameter_dict in enumerate(hyperparameter_dicts):
      assert hyperparameter_dict["alpha"] == old_hyperparameter_dict[i]["alpha"]
      assert hyperparameter_dict["task_length"] is None
      assert hyperparameter_dict["tikhonov"] is None
      self.assert_length_scales_valid(hyperparameter_dict["length_scales"], domain)
      for j, ls in enumerate(hyperparameter_dict["length_scales"]):
        assert ls == old_hyperparameter_dict[i]["length_scales"][j]
