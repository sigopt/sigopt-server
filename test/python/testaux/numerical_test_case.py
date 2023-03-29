# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy


DEFAULT_ABS_TOL = 1e-9  # if the absolute difference is bellow this value, values will be considered close


class NumericalTestCase(object):
  @staticmethod
  def assert_scalar_within_relative(value, truth, tol):
    denom = numpy.fabs(truth)
    if denom < 2.2250738585072014e-308:  # numpy.finfo(numpy.float64).tiny:
      denom = 1.0  # do not divide by 0
    diff = numpy.fabs((value - truth) / denom)
    assert diff <= tol, f"value = {value:.18E}, truth = {truth:.18E}, diff = {diff:.18E}, tol = {tol:.18E}"

  @staticmethod
  def assert_scalar_is_close(value, truth, tol, abs_tol=DEFAULT_ABS_TOL):
    diff = numpy.fabs(value - truth)
    is_close = numpy.isclose(value, truth, rtol=tol, atol=abs_tol)
    assert (
      is_close
    ), f"value = {value:.18E}, truth = {truth:.18E}\ndiff = {diff:.18E}, tol = {tol:.18E}, abs_tol = {abs_tol:.18E}"

  @staticmethod
  def assert_vector_within_relative(value, truth, tol):
    assert value.shape == truth.shape, f"value.shape = {value.shape} != truth.shape = {truth.shape}"
    for index in numpy.ndindex(value.shape):
      NumericalTestCase.assert_scalar_within_relative(value[index], truth[index], tol)

  @staticmethod
  def assert_vector_row_wise_norm_is_close(value, truth, tol, norm=2, abs_tol=DEFAULT_ABS_TOL):
    assert value.shape == truth.shape, f"value.shape = {value.shape} != truth.shape = {truth.shape}"
    value_norms = numpy.linalg.norm(value, axis=1, ord=norm)
    truth_norms = numpy.linalg.norm(truth, axis=1, ord=norm)
    diff = numpy.fabs(value_norms - truth_norms)
    denom = truth_norms
    bound = numpy.maximum(denom * tol, abs_tol)
    failed_assert = numpy.flatnonzero(diff > bound)
    for index in failed_assert:
      assert diff[index] <= max(tol * bound[index], abs_tol), (
        f"truth and value vectors are different on indices {failed_assert.tolist()}. First error: \n"
        f"value[{index}, :] = {value[index]}\n"
        f"truth[{index}, :] = {truth[index]}\n"
        f"diff norm = {diff[index]} <= max(tol = {tol} * {bound[index]}, abs_tol = {abs_tol})"
      )
    assert len(failed_assert) == 0

  @staticmethod
  def assert_vector_within_relative_norm(value, truth, tol, norm=2):
    assert value.shape == truth.shape, f"value.shape = {value.shape} != truth.shape = {truth.shape}"
    v = numpy.reshape(value, (numpy.prod(value.shape),))
    t = numpy.reshape(truth, (numpy.prod(truth.shape),))
    err = numpy.linalg.norm(v - t, ord=norm)
    mag = numpy.linalg.norm(t, ord=norm) if numpy.linalg.norm(t, ord=norm) > numpy.finfo(numpy.float64).eps else 1.0
    assert err / mag < tol, f"error = {err} / magnitude = {mag} > tol = {tol}"

  @staticmethod
  def check_gradient_with_finite_difference(x, func, grad, fd_step, tol, use_complex=False):
    """
        Approximate gradient using finite difference using either the centered method or complex step.
        """

    def fd_centered_method(x, func, fd_step, g_approx):
      x_plus_perturbation = x[:, :, None] + numpy.diag(fd_step)
      x_min_perturbation = x[:, :, None] - numpy.diag(fd_step)
      dim = x.shape[1]
      for i in range(dim):
        g_approx[:, i] = (func(x_plus_perturbation[:, :, i]) - func(x_min_perturbation[:, :, i])) / (2 * fd_step[i])
      return g_approx

    def fd_complex_step(x, func, fd_step, g_approx):
      dim = x.shape[1]
      z = x + 0j
      for i in range(dim):
        z[:, i] += fd_step[i] * 1j
        g_approx[:, i] = func(z).imag / fd_step[i]
        z[:, i] -= fd_step[i] * 1j
      return g_approx

    assert len(x.shape) == 2
    assert x.shape[1] == fd_step.shape[0]
    g = grad(x)
    if len(g.shape) == 1:
      g = g.reshape((1, -1))
    g_approx = numpy.empty_like(g)
    finite_difference_method = fd_complex_step if use_complex else fd_centered_method
    g_approx = finite_difference_method(x, func, fd_step, g_approx)
    NumericalTestCase.assert_vector_row_wise_norm_is_close(g_approx, g, tol)
