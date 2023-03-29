# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import scipy.linalg

from libsigopt.compute.misc.constant import NONZERO_MEAN_CONSTANT_MEAN_TYPE, NONZERO_MEAN_LINEAR_MEAN_TYPE


def indices_represent_zero_mean(indices_list):
  """Tests possible inputs to see if they correspond to the zero mean case. """

  return indices_list is None or numpy.asarray(indices_list, dtype=int).size == 0


def indices_represent_constant_mean(indices_list, dim):
  """Tests possible inputs to see if they correspond to the constant mean case."""
  return numpy.array_equal(indices_list, numpy.zeros((1, dim)))


def polynomial_index_point_check(indices_list, dim):
  r"""Confirm the user did not pass nonsensical polynomial power indices.

    This always checks to make sure that the indices are all the same dimension, and that they are all integers. Then it
    returns a numpy.array version of those indices.

    If the dimension of the points is passed as dim, then that dimension is compared to the dimension of the proposed
    polynomial to make sure they match.

    NOTE: You can pass indices_list=None if you also pass a dim to receive back the appropriate default
      integer array: numpy.empty((0,dim)), but you MUST pass a dim or this will error.

    """

  if indices_represent_zero_mean(indices_list):
    return numpy.empty((0, dim))
  else:
    indices_list = numpy.array(indices_list, dtype=int)
    if len(indices_list.shape) != 2 or indices_list.shape[1] != dim:
      raise ValueError(f"indices {indices_list} are unacceptable for dimension {dim}")
    return indices_list


def validate_polynomial_indices(polynomial_indices, nonzero_mean_type, dim):
  if nonzero_mean_type in (NONZERO_MEAN_CONSTANT_MEAN_TYPE, NONZERO_MEAN_LINEAR_MEAN_TYPE):
    polynomial_indices = [[0] * dim]
    if nonzero_mean_type == NONZERO_MEAN_LINEAR_MEAN_TYPE:
      polynomial_indices.extend([[int(j == k) for j in range(dim)] for k in range(dim)])
  polynomial_indices = polynomial_index_point_check(polynomial_indices, dim=dim)
  return polynomial_indices


def build_polynomial_matrix(indices_list, points):
  r"""Compute the matrix with desired polynomial terms at the desired points

    Each term in the polynomial is specified with a list in indices_list and occupies one column of the matrix
    Each point of evaluation is specified with a row in points and occupies one row of the matrix
    Example of indices_list: [[0,0],[0,1],[1,0],[0,2],[3,4]] would be b_0 + b_1*y + b_2*x + b_3*y^2 + b_4*x^3*y^4
    Example of matrix: indices_list = [[0,0],[1,2]], points = [[2,3],[4,1],[0,8]]
                       poly_mat = [[2^0*3^0, 2^1*3^2]
                                   [4^0*1^0, 4^1*1^2]
                                   [0^0*8^0, 0^1*8^2]]
    Each sub-list in indices_list should have length dim - one power for each dimension

    The size of this matrix is m-by-n where:
      m - number of points
      n - number of terms in the polynomial
      dim - dimension of the points, also length of each sub-array in indices

    indices_list can also be an empty list, in which case a zero-mean is assumed

    TODO(RTL-63): Improvements may be possible through better memory access ... see python_utils_test

    TODO(RTL-64): Do we need to be worried that the columns of P may not be linearly independent in higher dimensions?

    """
  m, dim = points.shape
  il = polynomial_index_point_check(indices_list, dim=dim)
  n = il.shape[0]

  if n == 0:
    return numpy.zeros((m, 1))
  elif indices_represent_constant_mean(indices_list, dim=dim):
    return numpy.ones((m, n))
  else:
    poly_mat = numpy.ones((m, n))
    for row, point in enumerate(points):
      for col, indices in enumerate(il):
        for this_point, this_index in zip(point, indices):
          poly_mat[row][col] *= pow(this_point, this_index)
    return poly_mat


def build_grad_polynomial_tensor(indices_list, points):
  r"""Compute the gradient of the polynomial matrix used in the nonzero mean fitting.

    The size of this tensor is m-by-n-by-dim where:
      m - number of points
      n - number of terms in the polynomial
      dim - dimension of the points, also length of each sub-array in indices

    TODO(RTL-65): Improvements may be possible through better memory access ... see python_utils_test

    Example: indices_list = [[0,0],[1,2]], points = [[2,3],[4,1],[0,8]]
      Recall that the outcome of build_polynomial_matrix(indices_list, points) is
                  poly_mat = [[2^0*3^0, 2^1*3^2]
                              [4^0*1^0, 4^1*1^2]
                              [0^0*8^0, 0^1*8^2]]
      so, the gpt (grad_poly_tensor) would be
        gpt[:,:,0] = [[0 * 3^0, 1*2^0 * 3^2]    gpt[:,:,1] = [[2^0 * 0, 2^1 * 2*3^1]
                      [0 * 1^0, 1*4^0 * 1^2]                  [4^0 * 0, 4^1 * 2*1^1]
                      [0 * 8^0, 1*0^0 * 8^2]]                 [0^0 * 0, 0^1 * 2*8^1]]
      We denote 0^0=1 as is the standard for polynomials.


    """
  m, dim = points.shape
  il = polynomial_index_point_check(indices_list, dim=dim)
  n = il.shape[0]

  if indices_represent_constant_mean(indices_list, dim=dim) or n == 0:
    return numpy.zeros((m, n, dim))
  else:
    grad_poly_ten = numpy.ones((m, n, dim))
    for row, point in enumerate(points):
      for col, indices in enumerate(il):
        for d in range(dim):
          for this_dim, (this_point, this_index) in enumerate(zip(point, indices)):
            if d != this_dim:
              grad_poly_ten[row][col][d] *= pow(this_point, this_index)
            else:
              if this_index == 0:
                grad_poly_ten[row][col][d] = 0
              else:
                grad_poly_ten[row][col][d] *= this_index * pow(this_point, this_index - 1)

  return grad_poly_ten


def compute_cholesky_for_gp_sampling(covariance_matrix):
  """This function computes the Cholesky factorization, using the SVD + QR in ill-conditioned settings.

    Ill-conditioning will arise when there is insufficient distance between points under consideration
    when computing the posterior covariance.  If the SVD + QR is used, the resulting L matrix may not be
    full-rank at numerical precision (some of the diagonal values could be ~O(1e-16)) and will not be
    full-rank if there are actually duplicate points under consideration.

    This function return a Cholesky factor L, such that covariance_matrix = LL^T. The Cholesky factor
    is used to sample from a Gaussian process by computing m + Lz, where m is the mean of the GP and
    z is distributed according to the unit normal N(0, I)
    """
  # pylint: disable=unexpected-keyword-arg
  try:
    chol_cov = scipy.linalg.cholesky(covariance_matrix, lower=True, overwrite_a=True, check_finite=False)
  except scipy.linalg.LinAlgError:
    U, E, _ = scipy.linalg.svd(covariance_matrix, overwrite_a=True, check_finite=False)
    chol_cov = U * numpy.sqrt(E)[None, :]
    chol_cov = scipy.linalg.qr(chol_cov.T, mode="r", overwrite_a=True, check_finite=False)[0].T
  # pylint: enable=unexpected-keyword-arg
  return chol_cov
