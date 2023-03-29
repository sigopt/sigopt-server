# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Implementations of covariance functions for use with log_likelihood and gaussian_process.

As a reminder, all radial covariances have dim + 1 hyperparameters: [alpha, l_1, l_2, ..., l_dim].  alpha is the
process variance and l_1, ..., l_dim are the length scales.  All these values must be positive.

NOTE: Should this have a specific domain on which the hyperparameters can live?  If it did we could
incorporate that into the check_hyperparameters function.

"""
import numpy

from libsigopt.compute.covariance_base import DifferentiableRadialCovariance, RadialCovariance
from libsigopt.compute.misc.constant import (
  C0_RADIAL_MATERN_COVARIANCE_TYPE,
  C2_RADIAL_MATERN_COVARIANCE_TYPE,
  C4_RADIAL_MATERN_COVARIANCE_TYPE,
  SQUARE_EXPONENTIAL_COVARIANCE_TYPE,
)


def _scale_difference_matrix(scale, difference_matrix):
  return scale[:, :, None] * difference_matrix


class SquareExponential(DifferentiableRadialCovariance):
  """Implement the Gaussian covariance function.

    The function is radially defined as:
      cov(x, z) = alpha * exp(-.5 * r ** 2)
    where r = sqrt((x - z)^T * L * (x - z)) where L is the diagonal matrix with i-th diagonal entry
      L_ii = 1/l_i ** 2

    This covariance object has ``dim+1`` hyperparameters: ``alpha, lengths_i``

    """

  covariance_type = SQUARE_EXPONENTIAL_COVARIANCE_TYPE

  def __init__(self, hyperparameters):
    super().__init__(hyperparameters)

  def eval_radial_kernel(self, distance_matrix_squared):
    return numpy.exp(-0.5 * distance_matrix_squared)

  def eval_radial_kernel_grad(self, distance_matrix_squared, difference_matrix):
    return _scale_difference_matrix(
      -numpy.exp(-0.5 * distance_matrix_squared),
      difference_matrix,
    ) / self._length_scales_squared

  def eval_radial_kernel_hparam_grad(self, distance_matrix_squared, difference_matrix):
    return _scale_difference_matrix(
      numpy.exp(-0.5 * distance_matrix_squared),
      (difference_matrix**2),
    ) / self._length_scales_cubed

  def _covariance(self, x, z):
    r, _ = self._distance_between_points(z, x)
    return numpy.exp(-0.5 * r**2)

  def _grad_covariance(self, x, z):
    r, dm = self._distance_between_points(z, x)
    r_2d = r[:, None]
    return -numpy.exp(-0.5 * r_2d**2) * dm / self._length_scales_squared

  def _hyperparameter_grad_covariance_without_process_variance(self, x, z):
    r, dm = self._distance_between_points(z, x)
    r_2d = r[:, None]
    return numpy.exp(-0.5 * r_2d**2) * (dm**2) / self._length_scales_cubed


class C0RadialMatern(RadialCovariance):
  """Implement the C0 radial Matern covariance function.

    The function is radially defined as:
      cov(x, z) = alpha * exp(-r)
    where r = sqrt((x - z)^T * L * (x - z)) where L is the diagonal matrix with i-th diagonal entry
      L_ii = 1/l_i ** 2

    This covariance object has ``dim+1`` hyperparameters: ``alpha, lengths_i``

    """

  covariance_type = C0_RADIAL_MATERN_COVARIANCE_TYPE

  def __init__(self, hyperparameters):
    super().__init__(hyperparameters)

  def eval_radial_kernel(self, distance_matrix_squared):
    r = numpy.sqrt(distance_matrix_squared)
    return numpy.exp(-r)

  def _covariance(self, x, z):
    r, _ = self._distance_between_points(z, x)
    return numpy.exp(-r)


class C2RadialMatern(DifferentiableRadialCovariance):
  """Implement the C2 radial Matern covariance function.

    The function is radially defined as:
      cov(x, z) = alpha * (1 + r) * exp(-r)
    where r = sqrt((x - z)^T * L * (x - z)) where L is the diagonal matrix with i-th diagonal entry
      L_ii = 1/l_i ** 2

    This covariance object has ``dim+1`` hyperparameters: ``alpha, lengths_i``

    """

  covariance_type = C2_RADIAL_MATERN_COVARIANCE_TYPE

  def __init__(self, hyperparameters):
    super().__init__(hyperparameters)

  def eval_radial_kernel(self, distance_matrix_squared):
    r = numpy.sqrt(distance_matrix_squared)
    return (1 + r) * numpy.exp(-r)

  def eval_radial_kernel_grad(self, distance_matrix_squared, difference_matrix):
    r = numpy.sqrt(distance_matrix_squared)
    return _scale_difference_matrix(-numpy.exp(-r), difference_matrix) / self._length_scales_squared

  def eval_radial_kernel_hparam_grad(self, distance_matrix_squared, difference_matrix):
    r = numpy.sqrt(distance_matrix_squared)
    return _scale_difference_matrix(numpy.exp(-r), difference_matrix**2) / self._length_scales_cubed

  def _covariance(self, x, z):
    r, _ = self._distance_between_points(z, x)
    return (1 + r) * numpy.exp(-r)

  def _grad_covariance(self, x, z):
    r, dm = self._distance_between_points(z, x)
    r_2d = r[:, None]
    return -numpy.exp(-r_2d) * dm / self._length_scales_squared

  def _hyperparameter_grad_covariance_without_process_variance(self, x, z):
    r, dm = self._distance_between_points(z, x)
    r_2d = r[:, None]
    return numpy.exp(-r_2d) * (dm**2) / self._length_scales_cubed


class C4RadialMatern(DifferentiableRadialCovariance):

  """Implement the C4 radial Matern covariance function.

    The function is radially defined as:
      cov(x, z) = alpha * (1 + r + .3333 * r^2) * exp(-r)
    where r = sqrt((x - z)^T * L * (x - z)) where L is the diagonal matrix with i-th diagonal entry
      L_ii = 1/l_i ** 2

    This covariance object has ``dim+1`` hyperparameters: ``alpha, lengths_i``

    """

  covariance_type = C4_RADIAL_MATERN_COVARIANCE_TYPE

  def __init__(self, hyperparameters):
    super().__init__(hyperparameters)

  def eval_radial_kernel(self, distance_matrix_squared):
    r = numpy.sqrt(distance_matrix_squared)
    return (1 + r + 1.0 / 3.0 * distance_matrix_squared) * numpy.exp(-r)

  def eval_radial_kernel_grad(self, distance_matrix_squared, difference_matrix):
    r = numpy.sqrt(distance_matrix_squared)
    return _scale_difference_matrix(
      -(1.0 / 3.0) * (1 + r) * numpy.exp(-r),
      difference_matrix,
    ) / self._length_scales_squared

  def eval_radial_kernel_hparam_grad(self, distance_matrix_squared, difference_matrix):
    r = numpy.sqrt(distance_matrix_squared)
    return _scale_difference_matrix(
      (1.0 / 3.0) * (1 + r) * numpy.exp(-r),
      (difference_matrix**2),
    ) / self._length_scales_cubed

  def _covariance(self, x, z):
    r, _ = self._distance_between_points(z, x)
    return (1 + r + 1.0 / 3.0 * r**2) * numpy.exp(-r)

  def _grad_covariance(self, x, z):
    r, dm = self._distance_between_points(z, x)
    r_2d = r[:, None]
    return -(1.0 / 3.0) * (1 + r_2d) * numpy.exp(-r_2d) * dm / self._length_scales_squared

  def _hyperparameter_grad_covariance_without_process_variance(self, x, z):
    r, dm = self._distance_between_points(z, x)
    r_2d = r[:, None]
    return (1.0 / 3.0) * (1 + r_2d) * numpy.exp(-r_2d) * (dm**2) / self._length_scales_cubed


COVARIANCE_TYPES_TO_CLASSES = {
  SQUARE_EXPONENTIAL_COVARIANCE_TYPE: SquareExponential,
  C4_RADIAL_MATERN_COVARIANCE_TYPE: C4RadialMatern,
  C2_RADIAL_MATERN_COVARIANCE_TYPE: C2RadialMatern,
  C0_RADIAL_MATERN_COVARIANCE_TYPE: C0RadialMatern,
}
