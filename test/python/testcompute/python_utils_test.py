# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Implementation (Python) of TestNonzeroMean to confirm the viability of nonzero mean GPs.

It also tests the functions build_polynomial_matrix and build_grad_polynomial_tensor.

"""

import numpy
import pytest
from flaky import flaky

from libsigopt.aux.samplers import generate_latin_hypercube_points
from libsigopt.compute.covariance import C4RadialMatern, SquareExponential
from libsigopt.compute.domain import ContinuousDomain
from libsigopt.compute.gaussian_process import GaussianProcess
from libsigopt.compute.misc.data_containers import HistoricalData
from libsigopt.compute.python_utils import (
  build_grad_polynomial_tensor,
  build_polynomial_matrix,
  compute_cholesky_for_gp_sampling,
  indices_represent_constant_mean,
  indices_represent_zero_mean,
  polynomial_index_point_check,
)
from testaux.numerical_test_case import DEFAULT_ABS_TOL, NumericalTestCase


class TestNonzeroMean(NumericalTestCase):

  num_points_list = (11, 14, 19, 22, 39, 50)
  num_poly_indices_list = (1, 1, 2, 3, 5, 8)
  num_dim_list = (5, 7, 4, 3, 2, 2)

  def test_polynomial_validation(self):
    assert indices_represent_zero_mean([[]]) and not indices_represent_zero_mean([[0]])
    for d in self.num_dim_list:
      assert indices_represent_constant_mean([[0] * d], d)
      assert not (indices_represent_constant_mean([[1] * d], d) or indices_represent_constant_mean([[0] * d], d + 1))
      assert indices_represent_zero_mean(polynomial_index_point_check(None, d))
    with pytest.raises(ValueError):
      polynomial_index_point_check([[0, 0], [1, 1]], 3)
    with pytest.raises(ValueError):
      polynomial_index_point_check([[0, 0], [1, 1, 1]], 3)
    with pytest.raises(ValueError):
      polynomial_index_point_check([1, 1, 1], 3)
    with pytest.raises(ValueError):
      polynomial_index_point_check([1, 1.3, 1], 3)

    for num_points, poly_length, dim in zip(self.num_points_list, self.num_poly_indices_list, self.num_dim_list):
      indices_list = numpy.random.randint(0, num_points, (poly_length, dim))
      assert numpy.array_equal(polynomial_index_point_check(indices_list, dim), indices_list)

  def polynomial_matrix_test(self, num_points, poly_length, dim):
    """Testing the accuracy of the polynomial matrix construction function.

        The function build_polynomial_matrix in python_utils is compared against a matrix
        constructed through elementwise products.

        We may eventually replace the loops in build_polynomial_matrix with this broadcast
        version depending on the relationship between speed and memory.  To do so we would
        need the indices_list to be a numpy.array instead of a list of lists.

        """

    domain = ContinuousDomain([[-1, 1]] * dim)
    points = domain.generate_quasi_random_points_in_domain(num_points)
    indices_list = numpy.random.randint(0, num_points, (poly_length, dim))

    p = build_polynomial_matrix(indices_list, points)
    p_prod = numpy.prod([pow(points[:, d][:, None], indices_list[:, d]) for d in range(dim)], 0)

    self.assert_vector_within_relative(p_prod, p, numpy.linalg.norm(p) * numpy.finfo(float).eps)

  def gradient_polynomial_tensor_test(self, num_points, poly_length, dim):
    """Testing the accuracy of the gradient polynomial tensor construction function.

        The function build_grad_polynomial_tensor in python_utils is compared against a matrix constructed through
        element-wise products.

        Note that we need to ()^+ the polynomial power to prevent computing a 1/x value which could be 1/0.
        That is what (indices_list[:, d] > 0)) does.

        To understand the loops, each dimension is stored in a 2D slice of a 4D tensor, with the appropriate derivative
        applied to correspond to the appropriate dimension.  So for a 2 dimensional problem, the d/dx_1 would have a
        derivative in the 0th slice but no derivative in the 1st slice.
        Then the slices are multiplied together to form the 3D tensor which contains 2D slices,
        the nth of which contains derivatives with respect to the nth dimension.

        In reality, the memory cost of this problem could be reduced by not redundantly storing copies of
        the non-derivative data as is currently done.  But, in doing so, there would be less efficient memory access
        - the logical extension of this idea is what is currently implemented.
        We'll need to think on this as it applies to the real problems.
        """

    domain = ContinuousDomain([[-1, 1]] * dim)
    points = domain.generate_quasi_random_points_in_domain(num_points)
    indices_list = numpy.random.randint(0, num_points, (poly_length, dim))

    gpt = build_grad_polynomial_tensor(indices_list, points)

    gpt_each_dim = numpy.empty((num_points, poly_length, dim, dim))
    for d in range(dim):
      for d_der in range(dim):
        if d != d_der:
          gpt_each_dim[:, :, d, d_der] = pow(points[:, d_der][:, None], indices_list[:, d_der])
        else:
          gpt_each_dim[:, :, d, d] = (
            pow(points[:, d][:, None], (indices_list[:, d] - 1) * (indices_list[:, d] > 0)) * indices_list[:, d]
          )
    gpt_prod = numpy.prod(gpt_each_dim, 3)

    self.assert_vector_within_relative(gpt_prod, gpt, numpy.linalg.norm(gpt) * numpy.finfo(float).eps)

  # Constant mean gets its own set of tests because it's our standard workflow for right now
  def constant_mean_components_test(self, num_points, dim):
    constant_indices = numpy.zeros((1, dim))
    self.assert_vector_within_relative(constant_indices, polynomial_index_point_check(constant_indices, dim), 0)
    assert indices_represent_constant_mean(constant_indices, dim)
    test_points = numpy.random.random((num_points, dim))
    self.assert_vector_within_relative(
      numpy.ones((num_points, 1)),
      build_polynomial_matrix(constant_indices, test_points),
      0,
    )
    self.assert_vector_within_relative(
      numpy.zeros((num_points, 1, dim)),
      build_grad_polynomial_tensor(constant_indices, test_points),
      0,
    )
    data = HistoricalData(dim)
    const_val = numpy.random.normal(numpy.random.random(), numpy.random.random(), 1)
    data.append_historical_data(
      points_sampled=test_points,
      points_sampled_value=numpy.full(num_points, const_val),
      points_sampled_noise_variance=numpy.full(num_points, 1e-10),
    )
    cov = C4RadialMatern(numpy.random.gamma(1, 0.1, dim + 1))
    gp = GaussianProcess(cov, data, constant_indices)
    new_points = numpy.random.random((2 * num_points, dim))
    self.assert_vector_within_relative(
      numpy.full(len(new_points), const_val),
      gp.compute_mean_of_points(new_points),
      1e-14,
    )

  @staticmethod
  def generate_random_data(dim, func, n, true_var=0.0, obs_var=0.0):
    """Creates random data on which we can test our functionality.

        This should probably either replace or be incorporated into build_test_gaussian_process but the
        process of sifting through the test framework will take an amount of time.

        """
    tv = numpy.full(n, true_var)
    domain = numpy.array([[0, 1]] * dim)

    # Note that the latin hypercube points have some randomness in them
    x = generate_latin_hypercube_points(n, domain)
    y = numpy.array([func(xval) for xval in x]) + tv * numpy.random.normal(size=n)

    ov = numpy.full(n, obs_var)
    historical_data = HistoricalData(dim=dim)
    historical_data.append_historical_data(points_sampled=x, points_sampled_value=y, points_sampled_noise_variance=ov)
    return historical_data, domain

  def test_polynomial_computations(self):
    """Run tests on polynomial function computation with a range of sizes."""

    for i, j, k in zip(self.num_points_list, self.num_poly_indices_list, self.num_dim_list):
      self.polynomial_matrix_test(i, j, k)
      self.gradient_polynomial_tensor_test(i, j, k)

  def test_constant_mean(self):
    for n, d in zip(self.num_points_list, self.num_dim_list):
      self.constant_mean_components_test(n, d)

  # The failure rate seems to be less than 1/1000
  @flaky(max_runs=2)
  def test_nonzero_mean_reproduction(self):
    """Confirm that our generalized least squares implementation works.

        Consider different sized sample problems and generate fake data for each of them. The fake data consists of
        a polynomial plus noise and the goal is to find the polynomial through the noise, up to a certain accuracy.
        We expect the coefficients of the polynomial mean to match the true coefficients up to the noise present in
        the data. The variance that is present in the data is augmented by the size of the data set and the dimension
        that the data exists in the data.  We give an error range of a factor of 10 and then throw an exception if the
        error is worse than that.

        Note that the choice of kernel hyperparameters could play a role here,
        which is why I am allowing them to be random.
        I suppose this is a weird way to test this concept, but I think the theory is still a bit off,
        so this will help support our beliefs in the interim.

        """

    for n, dim in zip(self.num_points_list, self.num_dim_list):
      if n < dim + 1:
        raise ValueError("At least dim+1 points must be passed to fit a linear mean")

      test_const_coef = numpy.random.normal(size=1)
      test_lin_coef = numpy.random.normal(size=dim)
      func = lambda x: test_const_coef[0] + numpy.dot(test_lin_coef, x)
      true_var = numpy.random.lognormal(mean=-10.0, sigma=3.0)
      obs_var = numpy.random.lognormal(mean=-12.0, sigma=3.0)
      historical_data, _ = self.generate_random_data(dim, func, n, true_var, obs_var)

      params = numpy.random.gamma(1, 0.1, dim + 1)
      kernel = SquareExponential(params)

      mean_indices = [[0] * dim]
      mean_indices.extend([[int(j == k) for j in range(dim)] for k in range(dim)])

      gp_linear_mean = GaussianProcess(kernel, historical_data, mean_indices)
      test_coef = numpy.concatenate((test_const_coef, test_lin_coef), axis=0)
      self.assert_vector_within_relative_norm(gp_linear_mean.poly_coef, test_coef, 10 * dim * n * true_var)


class TestCholeskyFactorization(NumericalTestCase):
  def assert_cholesky_is_accurate(self, cholesky_factor, original_matrix):
    self.assert_vector_within_relative_norm(
      numpy.dot(cholesky_factor, cholesky_factor.T),
      original_matrix,
      DEFAULT_ABS_TOL,
    )

  @pytest.mark.parametrize("size", [10, 50, 200])
  def test_well_conditioned_matrices(self, size):
    # Random positive definite matrix
    A = numpy.random.randn(size, size)
    P = numpy.dot(A, A.T) + numpy.eye(size)
    L = compute_cholesky_for_gp_sampling(P)
    self.assert_cholesky_is_accurate(L, P)

    # Real covariance matrix
    dim = 4
    X = numpy.random.rand(size, dim)
    params = numpy.random.gamma(1, 0.1, dim + 1)
    kernel = SquareExponential(params)
    covariance_matrix = kernel.build_kernel_matrix(X) + 1e-4 * numpy.eye(size)
    L = compute_cholesky_for_gp_sampling(covariance_matrix)
    self.assert_cholesky_is_accurate(L, covariance_matrix)

  @pytest.mark.parametrize("size", [10, 50, 200])
  def test_ill_conditioned_matrices(self, size):
    # Random ill conditioned matrix
    matrix_rank = 4
    X = numpy.random.rand(size, matrix_rank)
    P = numpy.dot(X, X.T)
    assert numpy.linalg.matrix_rank(P) == matrix_rank
    L = compute_cholesky_for_gp_sampling(P)
    self.assert_cholesky_is_accurate(L, P)

    # Real ill conditioned covariance matrix
    dim = 3
    X = 0.0001 * numpy.random.rand(size, dim)
    spatial_rank = 5
    X[:spatial_rank] = numpy.random.rand(spatial_rank, dim)
    kernel = SquareExponential(numpy.ones(dim + 1))
    covariance_matrix = kernel.build_kernel_matrix(X)
    assert numpy.linalg.matrix_rank(covariance_matrix) < size
    L = compute_cholesky_for_gp_sampling(covariance_matrix)
    self.assert_cholesky_is_accurate(L, covariance_matrix)
