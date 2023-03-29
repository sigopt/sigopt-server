# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from libsigopt.compute.predictor import HasPredictor


class AcquisitionFunction(HasPredictor):
  def __init__(self, predictor):
    super().__init__(predictor)

    self.best_value = predictor.best_observed_value
    self.best_location = predictor.best_observed_location

    # This is the number of points to be simultaneously considered for selection (not outstanding points)
    self.num_points_to_sample = 1

  def evaluate_at_point_list(self, points_to_evaluate, batch_size=None):
    eval_shape = points_to_evaluate.shape
    assert len(eval_shape) == (2 if self.num_points_to_sample == 1 else 3)
    assert eval_shape[-1] == self.dim
    batch_size = batch_size or eval_shape[0]
    assert int(batch_size) == batch_size and batch_size > 0

    current_index = 0
    eval_result = numpy.empty(eval_shape[0])
    while current_index < len(eval_result):
      indices = range(current_index, min(current_index + batch_size, len(eval_result)))
      eval_result[indices] = self._evaluate_at_point_list(points_to_evaluate[indices])
      current_index += len(indices)

    return eval_result

  def _evaluate_at_point_list(self, points_to_evaluate):
    raise NotImplementedError()

  # TODO(RTL-47): Actually implement the batch_size computation
  def evaluate_grad_at_point_list(self, points_to_evaluate, batch_size=None):
    assert self.differentiable

    eval_shape = points_to_evaluate.shape
    assert len(eval_shape) == 2
    assert eval_shape[-1] == self.dim
    assert batch_size is None

    return self._evaluate_grad_at_point_list(points_to_evaluate)

  def _evaluate_grad_at_point_list(self, points_to_evaluate):
    raise NotImplementedError()

  # Generally this will be more efficiently evaluated in child classes, but this should always work
  # TODO(RTL-48): Consider relevance of batch_size here ... eventually relevant in vectorized optimizers
  def joint_function_gradient_eval(self, points_to_evaluate):
    return self._evaluate_at_point_list(points_to_evaluate), self._evaluate_grad_at_point_list(points_to_evaluate)

  def append_lie_locations(self, lie_locations):
    eval_shape = lie_locations.shape
    assert len(eval_shape) == 2
    assert eval_shape[-1] == self.dim
    self._append_lie_locations(lie_locations)

  def _append_lie_locations(self, lie_locations):
    raise NotImplementedError()
