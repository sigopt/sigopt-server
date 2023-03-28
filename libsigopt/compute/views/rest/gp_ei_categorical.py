# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from libsigopt.aux.constant import PARALLEL_QEI
from libsigopt.compute.misc.constant import DEFAULT_MAX_SIMULTANEOUS_QEI_POINTS
from libsigopt.compute.multitask_acquisition_function import MultitaskAcquisitionFunction
from libsigopt.compute.views.view import GPView


class GpEiCategoricalView(GPView):
  view_name = "gp_ei_categorical"

  def view(self):
    assert self.has_optimization_metrics, f"{self.view_name} must have optimization metrics"
    max_simultaneous_af_points = self.params["model_info"].max_simultaneous_af_points
    parallelism = self.params["parallelism"]

    gaussian_process = self.form_gaussian_process_for_acquisition_function()
    num_being_sampled = len(self.one_hot_points_being_sampled_points)
    probabilistic_failures = self.form_probabilistic_failures_model()
    use_parallel_ei = (
      num_being_sampled > 0
      and parallelism == PARALLEL_QEI
    )
    expected_improvement_evaluator = self.form_acquisition_function(
      gaussian_process=gaussian_process,
      probabilistic_failures=probabilistic_failures,
      use_parallel_ei=use_parallel_ei,
    )
    if self.task_cost_populated:
      expected_improvement_evaluator = MultitaskAcquisitionFunction(expected_improvement_evaluator)

    if use_parallel_ei:
      max_simultaneous_af_points = min(max_simultaneous_af_points, DEFAULT_MAX_SIMULTANEOUS_QEI_POINTS)
    expected_improvement = expected_improvement_evaluator.evaluate_at_point_list(
      self.one_hot_points_to_evaluate_points,
      batch_size=max_simultaneous_af_points,
    )

    return {
      "endpoint": self.view_name,
      "expected_improvement": expected_improvement.tolist(),
      "tag": self.tag,
    }
