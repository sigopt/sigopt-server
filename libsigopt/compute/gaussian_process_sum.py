# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from libsigopt.compute.gaussian_process import GaussianProcess
from libsigopt.compute.misc.constant import CONSTANT_LIAR_MIN
from libsigopt.compute.predictor import Predictor


class GaussianProcessSum(Predictor):
  """
    This class implements a sum of weighted independent Gaussian Processes (GPs) such that:
      > sum_of_gps = w_1 GP_1(x) + w_2 GP_2(x) + ... w_n GP_n(x).
    We have assumed that the sampled points are the same for all GPs.
    This implementation does not compute much on its own, in fact, we just use the
    individual GPs to perform the bulk of computations.
    Notice that GPs are passed by reference. You should not change or share the GPs' HistoricalData
    """

  def __init__(self, gaussian_process_list, weights):
    assert len(gaussian_process_list) > 1, "We need more than one GP"
    assert len(gaussian_process_list) == len(weights), "Number of GPs and weights should match"
    first_gp = gaussian_process_list[0]
    for gp in gaussian_process_list:
      assert isinstance(gp, GaussianProcess)
      assert first_gp.dim == gp.dim
      assert numpy.allclose(first_gp.points_sampled, gp.points_sampled)
    self.gaussian_process_list = gaussian_process_list
    self.weights = weights
    self._best_index = None
    self._points_sampled_value_sum = None
    self._points_sampled_noise_variance_sum = None

  def __repr__(self):
    return (
      f"<{self.__class__.__module__}.{self.__class__.__name__} {hex(id(self))}>\n"
      f" weights={self.weights}\n"
      f" gaussain_process_list={self.gaussian_process_list}"
    )

  @property
  def best_index(self):
    if self._best_index is None:
      self._best_index = numpy.argmin(self.points_sampled_value)
    return self._best_index

  @property
  def best_observed_value(self):
    return self.points_sampled_value[self.best_index]

  @property
  def best_observed_location(self):
    return self.points_sampled[self.best_index, :]

  @property
  def differentiable(self):
    return all(gp.differentiable for gp in self.gaussian_process_list)

  @property
  def dim(self):
    return self.gaussian_process_list[0].dim

  @property
  def num_sampled(self):
    return self.gaussian_process_list[0].num_sampled

  @property
  def points_sampled(self):
    return self.gaussian_process_list[0].points_sampled

  @property
  def points_sampled_value(self):
    if self._points_sampled_value_sum is None:
      self._points_sampled_value_sum = self._compute_points_sampled_value_sum()
    return self._points_sampled_value_sum

  @property
  def points_sampled_noise_variance(self):
    if self._points_sampled_noise_variance_sum is None:
      self._points_sampled_noise_variance_sum = self._compute_points_sampled_noise_variance_sum()
    return self._points_sampled_noise_variance_sum

  def _compute_points_sampled_value_sum(self):
    points_sampled_value = numpy.zeros(self.num_sampled)
    for w, gp in zip(self.weights, self.gaussian_process_list):
      points_sampled_value = points_sampled_value + w * gp.points_sampled_value
    return points_sampled_value

  def _compute_points_sampled_noise_variance_sum(self):
    points_sampled_noise_variance = numpy.zeros(self.num_sampled)
    for w, gp in zip(self.weights, self.gaussian_process_list):
      points_sampled_noise_variance = points_sampled_noise_variance + (w**2) * gp.points_sampled_noise_variance
    return points_sampled_noise_variance

  def append_lie_data(self, lie_locations, lie_method=CONSTANT_LIAR_MIN):
    for gp in self.gaussian_process_list:
      gp.append_lie_data(lie_locations, lie_method)

  def compute_mean_of_points(self, points_to_sample):
    num_points = points_to_sample.shape[0]
    mean = numpy.zeros(num_points)
    for w, gp in zip(self.weights, self.gaussian_process_list):
      mean = mean + w * gp.compute_mean_of_points(points_to_sample)
    return mean

  def compute_variance_of_points(self, points_to_sample):
    num_points = points_to_sample.shape[0]
    var = numpy.zeros(num_points)
    for w, gp in zip(self.weights, self.gaussian_process_list):
      var = var + (w**2) * gp.compute_variance_of_points(points_to_sample)
    return var

  def compute_covariance_of_points(self, points_to_sample):
    num_points = points_to_sample.shape[0]
    covariance = numpy.zeros((num_points, num_points))
    for w, gp in zip(self.weights, self.gaussian_process_list):
      covariance = covariance + (w**2) * gp.compute_covariance_of_points(points_to_sample)
    return covariance

  def compute_mean_and_variance_of_points(self, points_to_sample):
    num_points = points_to_sample.shape[0]
    mean = numpy.zeros(num_points)
    var = numpy.zeros(num_points)
    for w, gp in zip(self.weights, self.gaussian_process_list):
      gp_mean, gp_var = gp.compute_mean_and_variance_of_points(points_to_sample)
      mean = mean + w * gp_mean
      var = var + (w**2) * gp_var
    return mean, var

  def compute_grad_mean_of_points(self, points_to_sample):
    num_points, dim = points_to_sample.shape
    grad_mean = numpy.zeros((num_points, dim))
    for w, gp in zip(self.weights, self.gaussian_process_list):
      grad_mean = grad_mean + w * gp.compute_grad_mean_of_points(points_to_sample)
    return grad_mean

  def compute_grad_variance_of_points(self, points_to_sample):
    num_points, dim = points_to_sample.shape
    grad_var = numpy.zeros((num_points, dim))
    for w, gp in zip(self.weights, self.gaussian_process_list):
      grad_var = grad_var + (w**2) * gp.compute_grad_variance_of_points(points_to_sample)
    return grad_var

  def compute_mean_variance_grad_of_points(self, points_to_sample):
    num_points, dim = points_to_sample.shape
    mean = numpy.zeros(num_points)
    var = numpy.zeros(num_points)
    grad_mean = numpy.zeros((num_points, dim))
    grad_var = numpy.zeros((num_points, dim))
    for w, gp in zip(self.weights, self.gaussian_process_list):
      gp_mean, gp_var, gp_grad_mean, gp_grad_var = gp.compute_mean_variance_grad_of_points(points_to_sample)
      mean = mean + w * gp_mean
      var = var + (w**2) * gp_var
      grad_mean = grad_mean + w * gp_grad_mean
      grad_var = grad_var + (w**2) * gp_grad_var
    return mean, var, grad_mean, grad_var

  def draw_posterior_samples_of_points(self, num_samples, points_to_sample):
    num_points = points_to_sample.shape[0]
    samples = numpy.zeros((num_samples, num_points))
    for w, gp in zip(self.weights, self.gaussian_process_list):
      samples = samples + w * gp.draw_posterior_samples_of_points(num_samples, points_to_sample)
    return samples
