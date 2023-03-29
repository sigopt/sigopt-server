# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from libsigopt.aux.constant import PARALLEL_CONSTANT_LIAR, PARALLEL_QEI
from libsigopt.compute.misc.constant import NONZERO_MEAN_CONSTANT_MEAN_TYPE
from libsigopt.compute.views.rest.gp_ei_categorical import GpEiCategoricalView
from testaux.numerical_test_case import NumericalTestCase
from testcompute.zigopt_input_utils import ZigoptSimulator


class AcquisitionFunctionTestBase(NumericalTestCase):
  def assert_call_successful(self, zigopt_simulator, parallelism_method):
    view_input = zigopt_simulator.form_gp_ei_categorical_inputs(parallelism_method)
    response = GpEiCategoricalView(view_input).call()
    assert len(response["expected_improvement"]) == len(view_input["points_to_evaluate"].points)
    assert [ei >= 0 for ei in response["expected_improvement"]]


class TestCategoricalConstantLiar(AcquisitionFunctionTestBase):
  @pytest.mark.parametrize("dim", [3, 7])
  @pytest.mark.parametrize("num_sampled", [19, 41])
  @pytest.mark.parametrize("num_to_sample", [26])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  @pytest.mark.parametrize(
    "num_constraint_metrics, constraint_metric_thresholds",
    [
      (0, None),
      (2, [0.1, -0.1]),
    ],
  )
  @pytest.mark.parametrize("num_stored_metrics", [0, 1])
  @pytest.mark.parametrize("num_being_sampled", [0, 3])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("use_tikhonov", [True, False])
  def test_constant_liar_base(
    self,
    dim,
    num_sampled,
    num_to_sample,
    num_optimized_metrics,
    num_constraint_metrics,
    num_stored_metrics,
    num_being_sampled,
    nonzero_mean_type,
    use_tikhonov,
    constraint_metric_thresholds,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_stored_metrics=num_stored_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=use_tikhonov,
      num_tasks=0,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    self.assert_call_successful(zs, PARALLEL_CONSTANT_LIAR)

  @pytest.mark.parametrize("dim", [4, 8])
  @pytest.mark.parametrize("num_sampled", [29, 43])
  @pytest.mark.parametrize("num_to_sample", [126])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  @pytest.mark.parametrize("num_being_sampled", [0, 7])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("use_tikhonov", [True, False])
  def test_constant_liar_multitask(
    self,
    dim,
    num_sampled,
    num_to_sample,
    num_optimized_metrics,
    num_being_sampled,
    nonzero_mean_type,
    use_tikhonov,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=use_tikhonov,
      num_tasks=3,
    )
    self.assert_call_successful(zs, PARALLEL_CONSTANT_LIAR)


class TestCategoricalQEI(AcquisitionFunctionTestBase):
  @pytest.mark.parametrize("dim", [5])
  @pytest.mark.parametrize("num_sampled", [22, 53])
  @pytest.mark.parametrize("num_to_sample", [159])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  @pytest.mark.parametrize(
    "num_constraint_metrics, constraint_metric_thresholds",
    [
      (0, None),
      (2, [0.1, -0.1]),
    ],
  )
  @pytest.mark.parametrize("num_being_sampled", [0, 3])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("use_tikhonov", [True, False])
  def test_qei_base(
    self,
    dim,
    num_sampled,
    num_to_sample,
    num_optimized_metrics,
    num_constraint_metrics,
    num_being_sampled,
    nonzero_mean_type,
    use_tikhonov,
    constraint_metric_thresholds,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_constraint_metrics=num_constraint_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=use_tikhonov,
      num_tasks=0,
      constraint_metric_thresholds=constraint_metric_thresholds,
    )
    self.assert_call_successful(zs, PARALLEL_QEI)

  @pytest.mark.parametrize("dim", [6])
  @pytest.mark.parametrize("num_sampled", [27, 62])
  @pytest.mark.parametrize("num_to_sample", [222])
  @pytest.mark.parametrize("num_optimized_metrics", [1, 2])
  @pytest.mark.parametrize("num_being_sampled", [0, 4])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("use_tikhonov", [False])
  def test_qei_multitask(
    self,
    dim,
    num_sampled,
    num_to_sample,
    num_optimized_metrics,
    num_being_sampled,
    nonzero_mean_type,
    use_tikhonov,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=num_optimized_metrics,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=use_tikhonov,
      num_tasks=4,
    )
    self.assert_call_successful(zs, PARALLEL_QEI)

  @pytest.mark.parametrize("dim", [7])
  @pytest.mark.parametrize("num_sampled", [12, 43])
  @pytest.mark.parametrize("num_to_sample", [111])
  @pytest.mark.parametrize("num_being_sampled", [0, 2])
  @pytest.mark.parametrize("nonzero_mean_type", [NONZERO_MEAN_CONSTANT_MEAN_TYPE])
  @pytest.mark.parametrize("use_tikhonov", [False])
  @pytest.mark.parametrize("parallelism_method", [PARALLEL_QEI, PARALLEL_CONSTANT_LIAR])
  def test_ei_no_optimized_metrics(
    self,
    dim,
    num_sampled,
    num_to_sample,
    num_being_sampled,
    nonzero_mean_type,
    use_tikhonov,
    parallelism_method,
  ):
    zs = ZigoptSimulator(
      dim=dim,
      num_sampled=num_sampled,
      num_optimized_metrics=0,
      num_to_sample=num_to_sample,
      num_being_sampled=num_being_sampled,
      nonzero_mean_type=nonzero_mean_type,
      use_tikhonov=use_tikhonov,
      num_tasks=0,
    )
    with pytest.raises(AssertionError):
      self.assert_call_successful(zs, parallelism_method)
