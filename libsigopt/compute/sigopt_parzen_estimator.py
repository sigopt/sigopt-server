# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy

import numpy

from libsigopt.compute.covariance_base import DifferentiableCovariance, RadialCovariance
from libsigopt.compute.optimization import ScipyOptimizable


SPE_MINIMUM_LOWER_DENSITY_VALUE = 1e-10
SPE_MINIMUM_LOWER_POINT_TOTAL = 3
SPE_MINIMUM_UNFORGOTTEN_POINT_TOTAL = 10


class SPEInsufficientDataError(Exception):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)


# points_sampled is PENextPoints style, not a HistoricalData object

# Inputs
# lower_covariance: the covariance associated with the lower density
# greater_covariance: the covariance associated with the greater density
# points_sampled: duh
# gamma:         the value to split the data into greater and lower densities (gamma proportion of the data in lower)
# forget_factor: the proportion of the earlier data to be "forgotten" when finding lower/greater
#                the points are assumed to be ordered with the earliest points in the first rows
class SigOptParzenEstimator(ScipyOptimizable):
  def __init__(
    self,
    lower_covariance,
    greater_covariance,
    points_sampled_points,
    points_sampled_values,
    gamma,
    forget_factor=0.0,
  ):
    assert 0 < gamma < 1
    assert 0 <= forget_factor < 1
    self.gamma = gamma
    self.forget_factor = forget_factor
    self.dim = len(points_sampled_points[0])
    self.lower_points = None
    self.greater_points = None

    # This is a list of 1D numpy.arrays full of lies to tell the model
    self.lower_lies = []
    self.greater_lies = []

    self.update_covariances(lower_covariance, greater_covariance)

    # This is to allow for the optimizer to run (maybe could just have current_point)
    self.point_to_sample = numpy.empty((0, self.dim))

    self.num_points = None  # Will be set in the function below
    self.form_model(
      points_sampled_points,
      points_sampled_values,
    )

  @property
  def differentiable(self):
    return (
      isinstance(self.lower_covariance, DifferentiableCovariance)
      and isinstance(self.greater_covariance, DifferentiableCovariance)
    )

  def __repr__(self):
    return (
      f"gamma={self.gamma}, |lower|={len(self.lower_points)}, |greater|={len(self.greater_points)}\n"
      f"lower_covariance={repr(self.lower_covariance)}\n"
      f"greater_covariance={repr(self.greater_covariance)}\n"
    )

  def get_current_point(self):
    return self.point_to_sample

  def set_current_point(self, current_point):
    self.point_to_sample = current_point

  current_point = property(get_current_point, set_current_point)

  def update_covariances(self, lower_covariance, greater_covariance):
    # NOTE: This radial check is not really necessary, but is beneficial at least for now
    assert isinstance(lower_covariance, RadialCovariance) and isinstance(greater_covariance, RadialCovariance)
    assert greater_covariance.dim == lower_covariance.dim == self.dim
    self.lower_covariance = lower_covariance
    self.greater_covariance = greater_covariance

  def append_lies(self, list_of_lying_arrays, lower=False):
    if list_of_lying_arrays:
      if lower:
        self.lower_lies.extend(list_of_lying_arrays)
        self.lower_points = numpy.concatenate((self.lower_points, numpy.atleast_2d(list_of_lying_arrays)))
      else:
        self.greater_lies.extend(list_of_lying_arrays)
        self.greater_points = numpy.concatenate((self.greater_points, numpy.atleast_2d(list_of_lying_arrays)))

  def clear_lies(self):
    if self.lower_lies:
      self.lower_points = self.lower_points[: -len(self.lower_lies), :]
    if self.greater_lies:
      self.greater_points = self.greater_points[: -len(self.greater_lies), :]
    self.lower_lies = []
    self.greater_lies = []

  def stash_lies(self):
    return deepcopy(self.lower_lies), deepcopy(self.greater_lies)

  def recover_lies(self, lie_info):
    lower_lies, greater_lies = lie_info
    self.clear_lies()
    self.append_lies(lower_lies, lower=True)
    self.append_lies(greater_lies, lower=False)

  # TODO(RTL-69): This can all be cleaned up now that we're not passing an iterator in
  def form_model(
    self,
    points_sampled_points,
    points_sampled_values,
  ):
    num_points = len(points_sampled_points)
    num_points_forgotten = int(self.forget_factor * num_points)
    if num_points - num_points_forgotten < SPE_MINIMUM_UNFORGOTTEN_POINT_TOTAL:
      raise SPEInsufficientDataError(f"num_points: {num_points}")

    # NOTE: The ordering is reversed from the observation_iterator
    self.num_points = num_points - num_points_forgotten
    values = points_sampled_values[: self.num_points]
    points = points_sampled_points[: self.num_points]

    indexes = numpy.argsort(values)
    data = points[indexes, :]

    sub_seq_len = max(int(self.num_points * self.gamma), SPE_MINIMUM_LOWER_POINT_TOTAL)
    if sub_seq_len > self.num_points - 1:
      raise SPEInsufficientDataError(f"gamma: {self.gamma}, num_points: {self.num_points}")
    self.lower_points = data[:sub_seq_len]
    self.greater_points = data[sub_seq_len:]

  def evaluate_lower_density(self, points_to_sample, grad=False):
    density = self._evaluate_base(
      points_to_sample=points_to_sample,
      points_sampled=self.lower_points,
      covariance=self.lower_covariance,
      grad=grad,
    )
    return density + SPE_MINIMUM_LOWER_DENSITY_VALUE

  def evaluate_greater_density(self, points_to_sample, grad=False):
    density = self._evaluate_base(
      points_to_sample=points_to_sample,
      points_sampled=self.greater_points,
      covariance=self.greater_covariance,
      grad=grad,
    )
    return density

  def _evaluate_base(self, points_to_sample, points_sampled, covariance, grad=False):
    if grad:
      assert self.differentiable
      density = numpy.mean(covariance.build_kernel_grad_tensor(points_sampled, points_to_sample), axis=1)
    else:
      density = numpy.mean(covariance.build_kernel_matrix(points_sampled, points_to_sample), axis=1)
    return density

  def evaluate_expected_improvement(self, points_to_sample):
    lpdf = self.evaluate_lower_density(points_to_sample)
    gpdf = self.evaluate_greater_density(points_to_sample)

    return lpdf, gpdf, 1 / (self.gamma + gpdf / lpdf * (1 - self.gamma))

  def compute_objective_function(self):
    return self.evaluate_expected_improvement(numpy.atleast_2d(self.point_to_sample))[2][0]

  def evaluate_grad_expected_improvement(self, points_to_sample):
    lpdf, gpdf, ei = self.evaluate_expected_improvement(points_to_sample)
    lpdf = lpdf[:, None]
    gpdf = gpdf[:, None]
    ei = ei[:, None]
    lpdf_g = self.evaluate_lower_density(points_to_sample, grad=True)
    gpdf_g = self.evaluate_greater_density(points_to_sample, grad=True)

    return -(ei**2) * (1 - self.gamma) * (lpdf * gpdf_g - gpdf * lpdf_g) / lpdf**2

  def compute_grad_objective_function(self):
    return self.evaluate_grad_expected_improvement(numpy.atleast_2d(self.point_to_sample))[0]
