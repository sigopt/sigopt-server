# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from libsigopt.compute.acquisition_function import AcquisitionFunction


# The underlying AF will need to be in phys_dim + 1 dimensions, where the last column is the task column.
# TODO - Convert this into an EI-penalty (which probably means a more general AF penalty)
class MultitaskAcquisitionFunction(AcquisitionFunction):
  def __init__(self, acquisition_function):
    super().__init__(acquisition_function.predictor)
    assert isinstance(acquisition_function, AcquisitionFunction)
    self.underlying = acquisition_function

  @property
  def dim(self):
    return self.underlying.dim

  @property
  def differentiable(self):
    return self.underlying.differentiable

  def _evaluate_at_point_list(self, points_to_evaluate):
    # pylint: disable=protected-access
    af_vals = self.underlying._evaluate_at_point_list(points_to_evaluate)
    # pylint: enable=protected-access
    task_costs = points_to_evaluate[:, -1]
    return af_vals / task_costs

  def joint_function_gradient_eval(self, points_to_evaluate):
    af_vals, af_val_grad = self.underlying.joint_function_gradient_eval(points_to_evaluate)
    task_costs = points_to_evaluate[:, -1]

    af_per_cost = af_vals / task_costs
    af_val_grad[:, :-1] /= task_costs[:, None]
    af_val_grad[:, -1] = (af_val_grad[:, -1] - af_per_cost) / task_costs
    return af_per_cost, af_val_grad

  def _evaluate_grad_at_point_list(self, points_to_evaluate):
    return self.joint_function_gradient_eval(points_to_evaluate)[1]

  def _append_lie_locations(self, lie_locations):
    self.underlying.append_lie_locations(lie_locations)
