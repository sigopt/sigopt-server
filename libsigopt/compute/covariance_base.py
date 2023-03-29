# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
r"""Base class covariance function: covariance of two points and spatial/hyperparameter derivatives.

Also implements specialized child covariances such as radial, differentiable.

Covariance functions have hyperparameters (e.g., signal/background noise, length scales) that specify the
assumed behavior of the Gaussian Process.  We use some optimization strategies (likelihood, CV) to find optimal
choices based on the data.
"""
import numpy
from scipy.spatial.distance import pdist, squareform

from libsigopt.aux.geometry_utils import compute_distance_matrix_squared


class HyperparameterInvalidError(ValueError):
  """Raised when hyperparameters of a covariance class are not all positive."""


class CovarianceBase(object):
  r"""Base class for covariance kernels; the functions that all covariance kernels must have."""

  covariance_type = NotImplemented
  process_variance = None

  @property
  def num_hyperparameters(self):
    raise NotImplementedError()

  @property
  def dim(self):
    raise NotImplementedError()

  @property
  def translation_invariant(self):
    """Defines whether the covariance has the form K(x, z) = phi(x - z)"""
    return NotImplemented

  def get_hyperparameters(self):
    raise NotImplementedError()

  def set_hyperparameters(self, hyperparameters):
    raise NotImplementedError()

  hyperparameters = property(get_hyperparameters, set_hyperparameters)

  def _covariance(self, x, z):
    """
        This is the internal implementation, computing the vector of covariance values
        """
    raise NotImplementedError

  def covariance(self, x, z):
    """Compute the covariance K(x,z).
        This accepts in two 2D arrays of points, and returns v[i] = K(x_i, z_i).

        """
    assert len(x.shape) == len(z.shape) == 2
    n, d = x.shape
    assert n == z.shape[0]
    assert self.dim == d == z.shape[1]

    covariance_vector = self._covariance(x, z)
    assert len(covariance_vector) == n

    return self.process_variance * covariance_vector

  def _build_kernel_matrix(self, points_sampled, points_to_sample=None):
    """
        This is the internal implementation, computing the K matrix without the process variance or noise on diagonal.
        """
    raise NotImplementedError

  def build_kernel_matrix(self, points_sampled, points_to_sample=None, noise_variance=None):
    """Compute the kernel matrix, K(x_i, z_j) for points_to_sample x_i and points_sampled z_j.

        If points_to_sample==None then the symmetric matrix with z_j for both rows and columns is created.

        The noise_variance is only applied in the symmetric case; if passed in the rectangular case this errors.  In the
        symmetric case, it adds the noise_variance to the diagonal.

        """
    kernel_matrix = self.process_variance * self._build_kernel_matrix(points_sampled, points_to_sample)

    if noise_variance is not None:
      nx, nz = kernel_matrix.shape
      assert nx == nz  # Or else there should be no noise_variance term because it would be meaningless
      kernel_matrix.flat[:: nx + 1] += noise_variance
    return kernel_matrix


class DifferentiableCovariance(CovarianceBase):

  """Class for virtual definitions of kernel derivative functions."""

  def _grad_covariance(self, x, z):
    raise NotImplementedError

  def grad_covariance(self, x, z):
    """Compute the gradient of the covariance K(x,z) wrt the dimensions in x.

        This accepts in two 2D arrays of points, and returns v[i, j] = grad_j K(x_i, z_i),
        where grad_j is the derivative wrt to the jth dimension of the x point (first argument).

        """
    assert len(x.shape) == len(z.shape) == 2
    n, d = x.shape
    assert n == z.shape[0]
    assert self.dim == d == z.shape[1]

    grad_covariance_vector = self._grad_covariance(x, z)
    assert grad_covariance_vector.shape == (n, d)

    return self.process_variance * grad_covariance_vector

  def _hyperparameter_grad_covariance_without_process_variance(self, x, z):
    """This function excludes the derivative wrt process_variance, which is dealt with in the function below."""
    raise NotImplementedError

  def hyperparameter_grad_covariance(self, x, z):
    """Compute the gradient of the covariance K(x,z) wrt the hyperparameters.

        This accepts in two 2D arrays of points, and returns v[i, j] = grad_j K(x_i, z_i),
        where grad_j is the derivative wrt to the jth hyperparameter.
        v[:, 0] is the derivative wrt the process variance, and v[:, j] is the derivative wrt l_j for j=1..n.

        """
    assert len(x.shape) == len(z.shape) == 2
    n, d = x.shape
    assert n == z.shape[0]
    assert self.dim == d == z.shape[1]

    hyperparameter_grad_covariance = numpy.empty((n, self.num_hyperparameters))
    hyperparameter_grad_covariance[:, 0] = self._covariance(x, z)
    hyperparameter_grad_covariance[:, 1:] = (
      self.process_variance * self._hyperparameter_grad_covariance_without_process_variance(x, z)
    )

    return hyperparameter_grad_covariance

  def _build_kernel_grad_tensor(self, points_sampled, points_to_sample=None):
    raise NotImplementedError()

  def build_kernel_grad_tensor(self, points_sampled, points_to_sample=None):
    r"""Compute the gradient wrt physical dimensions of a kernel matrix, as stored in a 3D tensor.

        The tensor returned is Kgrad[:, :, d] = grad_d Kmat, for Kmat from build_radial_kernel_matrix.

        """
    return self.process_variance * self._build_kernel_grad_tensor(points_sampled, points_to_sample)

  def _build_kernel_hparam_grad_tensor_without_process_variance(self, points_sampled, points_to_sample=None):
    raise NotImplementedError()

  def build_kernel_hparam_grad_tensor(self, points_sampled, points_to_sample=None):
    r"""Compute the gradient wrt the hyperparameters of a kernel matrix, as stored in a 3D tensor.

        The tensor returned is Khgrad, based on Kmat from build_radial_kernel_matrix.  Khgrad[:, :, 0] is the derivative
        wrt to the process variance alpha, and Khgrad[:, :, d+1] is the derivative wrt to the dth length scale.

        """
    n_cols, _ = points_sampled.shape
    n_rows = n_cols if points_to_sample is None else len(points_to_sample)

    kg_tensor = numpy.empty((n_rows, n_cols, self.num_hyperparameters))
    kg_tensor[:, :, 0] = self._build_kernel_matrix(points_sampled, points_to_sample)
    kg_tensor[:, :, 1:] = (
      self.process_variance
      * self._build_kernel_hparam_grad_tensor_without_process_variance(points_sampled, points_to_sample)
    )

    return kg_tensor


class RadialCovariance(CovarianceBase):

  """Class defining functions relevant only to radial kernels.

    Every radial kernel must have a process variance alpha and length scales l_i.  They are passed to this class as an
    array [alpha, l_1, l_2, ..., l_dim], where dim is the dimension of the physical space of interest.

    """
  def __init__(self, hyperparameters):
    self._hyperparameters = None
    self._length_scales = None
    self._length_scales_squared = None
    self._length_scales_cubed = None
    self.process_variance = None

    self.set_hyperparameters(hyperparameters)

  def __str__(self):
    return f"{self.__class__.__name__}_{self.dim}({self.hyperparameters})"

  def check_hyperparameters_are_valid(self, new_hyperparameters):
    new_hyperparameters = numpy.asarray(new_hyperparameters, dtype=float)
    assert len(new_hyperparameters.shape) == 1, f"Hyperparameters should be in 1D array, not {new_hyperparameters}"
    if (
      numpy.any(numpy.isnan(new_hyperparameters))
      or numpy.any(numpy.isinf(new_hyperparameters))
      or numpy.any(new_hyperparameters <= 0)
    ):
      raise HyperparameterInvalidError()
    return new_hyperparameters

  @property
  def num_hyperparameters(self):
    return self._hyperparameters.size

  @property
  def dim(self):
    return len(self._length_scales)

  @property
  def translation_invariant(self):
    return True

  def __repr__(self):
    return f"{self.covariance_type}({self._hyperparameters.tolist()})"

  def get_hyperparameters(self):
    return numpy.copy(self._hyperparameters)

  def set_hyperparameters(self, hyperparameters):
    self._hyperparameters = self.check_hyperparameters_are_valid(hyperparameters)
    self.process_variance = self._hyperparameters[0]
    self._length_scales = numpy.copy(self._hyperparameters[1:])
    self._length_scales_squared = self._length_scales**2
    self._length_scales_cubed = self._length_scales**3

  hyperparameters = property(get_hyperparameters, set_hyperparameters)

  def eval_radial_kernel(self, distance_matrix_squared):
    """Compute the covariance as a function of r^2."""
    raise NotImplementedError()

  def _distance_between_points(self, data, eval_points):
    """Evaluate the distances between points, as needed for the covariance evaluation.

        This function should only be needed in the covariance evaluation, not the radial evaluations.

        The distances computed are the weighted Euclidean distances, similarly to the _build_distance_matrix_squared.

        We require the data and eval_points to be the same size, and return the distance between them.

        If build_diff_vectors == False, the distance is returned as an array.
        If True, the distance that is returned is a "column vector", with shape (n, 1),
        for easy broadcasting to the diff_vecs.

        """
    data_shape = data.shape
    eval_shape = eval_points.shape
    if len(data_shape) != 2 or len(eval_shape) != 2:
      raise ValueError(f"Points must be a 2D array: data.shape = {data_shape}, eval_points.shape = {eval_shape}")
    elif data_shape != eval_shape:
      raise ValueError(f"Data size {data_shape}, Eval size {eval_shape}")
    elif data_shape[1] != self.dim:
      raise ValueError(f"Points dimension {data_shape[1]}, Covariance dimension {self.dim}")

    diff_vecs = eval_points - data
    r = numpy.sqrt(numpy.sum(numpy.power(diff_vecs / self._length_scales, 2), axis=1))
    return r, diff_vecs

  # customlint: disable=AccidentalFormatStringRule
  def _build_distance_matrix_squared(
    self,
    data,
    eval_points=None,
    build_diff_matrices=False,
  ):
    """Creates the distance matrices (and difference matrices) needed by radial kernels.

        We denote x as the eval_points and z as the data
        Distance matrices are of the form DM_{i,j} = sum_{k=1}^dim ((x_ik - z_jk)/ell_k)^2
        Difference matrices involve only a single dimension, without length scales: DiffM^(k)_{i,j} = x_ik - z_jk

        If you do not pass eval_points, we use eval_points == data, which is the symmetric covariance matrix.

        TODO(RTL-49): For large N and small d, the pdist function can actually be faster ...
        consider putting this logic in

        """
    if eval_points is None:
      return self._build_symmetric_distance_matrix_squared(data, build_diff_matrices)
    else:
      return self._build_nonsymmetric_distance_matrix_squared(data, eval_points, build_diff_matrices)

  def _build_symmetric_distance_matrix_squared(self, data, build_diff_matrices):
    diff_mats = None
    dist_mat_sq = squareform(pdist(data / self._length_scales[None, :], "sqeuclidean"))
    if build_diff_matrices:
      diff_mats = data[:, None, :] - data[None, :, :]
    return dist_mat_sq, diff_mats

  def _build_nonsymmetric_distance_matrix_squared(self, data, eval_points, build_diff_matrices):
    diff_mats = None
    x = eval_points / self._length_scales[None, :]
    z = data / self._length_scales[None, :]
    dist_mat_sq = compute_distance_matrix_squared(x, z)
    if build_diff_matrices:
      diff_mats = eval_points[:, None, :] - data[None, :, :]
    return dist_mat_sq, diff_mats

  def _build_kernel_matrix(self, points_sampled, points_to_sample=None):
    return self.eval_radial_kernel(self._build_distance_matrix_squared(points_sampled, points_to_sample)[0])


class DifferentiableRadialCovariance(DifferentiableCovariance, RadialCovariance):
  def eval_radial_kernel_grad(self, distance_matrix_squared, difference_matrix):
    """Compute the gradient of the covariance as a function of r^2."""
    raise NotImplementedError()

  def eval_radial_kernel_hparam_grad(self, distance_matrix_squared, difference_matrix):
    """Compute the gradient with respect to length scale of the covariance as a function of r^2.

        This can be used during hyperparameter optimization.

        """
    raise NotImplementedError()

  def _build_kernel_grad_tensor(self, points_sampled, points_to_sample=None):
    """Compute the gradient wrt physical dimensions of a kernel matrix, as stored in a 3D tensor."""
    dm_sq, diff_mats = self._build_distance_matrix_squared(points_sampled, points_to_sample, True)
    return self.eval_radial_kernel_grad(dm_sq, diff_mats)

  def _build_kernel_hparam_grad_tensor_without_process_variance(self, points_sampled, points_to_sample=None):
    """Compute the gradient wrt the hyperparameters of a kernel matrix, as stored in a 3D tensor."""
    dm_sq, diff_mats = self._build_distance_matrix_squared(points_sampled, points_to_sample, True)
    return self.eval_radial_kernel_hparam_grad(dm_sq, diff_mats)
