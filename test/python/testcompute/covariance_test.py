# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
"""Test cases for the covariance functions and any potential gradients.

TODO(RTL-86): Think about the need viability of a test specifically for radial kernels.  Something involving the radial
  Fourier transform, maybe.

"""
import inspect
import itertools

import numpy
import pytest
from flaky import flaky

from libsigopt.compute import covariance
from libsigopt.compute.covariance_base import DifferentiableCovariance, HyperparameterInvalidError
from libsigopt.compute.misc.constant import COVARIANCE_TYPES, TASK_LENGTH_LOWER_BOUND
from libsigopt.compute.multitask_covariance import MultitaskTensorCovariance
from testaux.numerical_test_case import NumericalTestCase


class CovariancesTestBase(NumericalTestCase):
  @classmethod
  @pytest.fixture(autouse=True, scope="class")
  def base_setup(cls):
    cls._base_setup()

  @classmethod
  def _base_setup(cls):
    cls.all_covariance_bases = [
      f[1]
      for f in inspect.getmembers(covariance, inspect.isclass)
      if getattr(f[1], "covariance_type") != NotImplemented
    ]
    cls.all_covariances = []
    for covariance_base in cls.all_covariance_bases:
      cls.all_covariances.append(covariance_base)
    cls.differentiable_covariances = [
      f for f in cls.all_covariances if inspect.isclass(f) and issubclass(f, DifferentiableCovariance)
    ]

    num_tests = 10
    dim_array = numpy.random.randint(1, 11, (num_tests,)).tolist()
    num_points_array = numpy.random.randint(30, 80, (num_tests,)).tolist()
    cls.test_z = []
    cls.test_x = []
    cls.test_hparams = []
    for dim, num_points in zip(dim_array, num_points_array):
      cls.test_z.append(numpy.random.random((num_points, dim)))
      cls.test_x.append(numpy.random.random((num_points - 10, dim)))
      cls.test_hparams.append(numpy.random.random((dim + 1,)))


class TestCovariances(CovariancesTestBase):
  def test_covariance_symmetric(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      z_trunc = z[: len(x), :]
      for covariance_object in self.all_covariances:
        cov = covariance_object(hparams)
        kernel_at_xz = cov.covariance(x, z_trunc)
        kernel_at_zx = cov.covariance(z_trunc, x)
        self.assert_vector_within_relative(kernel_at_xz, kernel_at_zx, 1e-8)

  def test_grad_covariance_antisymmetric(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      xn, d = x.shape
      zn, _ = z.shape
      full_zx = numpy.tile(z, (xn, 1))
      full_xz = numpy.reshape(numpy.tile(x, (1, zn)), (xn * zn, d))
      for covariance_object in self.differentiable_covariances:
        cov = covariance_object(hparams)
        basic_gtensor = cov.grad_covariance(full_xz, full_zx)
        basic_gtensor_flipped = cov.grad_covariance(full_zx, full_xz)
        self.assert_vector_within_relative(
          -basic_gtensor_flipped,
          basic_gtensor,
          1e-8,
        )

  @flaky(max_runs=2)
  def test_kernel_matrix_evaluation(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      xn, d = x.shape
      zn, _ = z.shape
      full_zx = numpy.tile(z, (xn, 1))
      full_xz = numpy.reshape(numpy.tile(x, (1, zn)), (xn * zn, d))
      full_zz = numpy.tile(z, (zn, 1))
      full_zz_trans = numpy.reshape(numpy.tile(z, (1, zn)), (zn * zn, d))
      # Note that, because of the faster computation that we use to compute kernel
      # matrices, it's possible the diagonal errors scale with sqrt(machine precision)
      # In reality, probably never gonna be close to this, but even this accuracy is much higher than need be
      for covariance_object in self.all_covariances:
        cov = covariance_object(hparams)
        standard_kernel_matrix = cov.build_kernel_matrix(z, x)
        basic_kernel_matrix = cov.covariance(full_xz, full_zx)
        self.assert_vector_within_relative_norm(
          standard_kernel_matrix.reshape(-1),
          basic_kernel_matrix,
          d * xn * zn * 1e-8,
        )
        standard_symm_kernel_matrix = cov.build_kernel_matrix(z)
        basic_symm_kernel_matrix = cov.covariance(full_zz, full_zz_trans)
        self.assert_vector_within_relative_norm(
          standard_symm_kernel_matrix.reshape(-1),
          basic_symm_kernel_matrix,
          d * zn * zn * 1e-8,
        )
        noise = numpy.full(zn, numpy.random.random() * 1e-4)
        standard_symmetric_noisy_kernel_matrix = cov.build_kernel_matrix(z, noise_variance=noise)
        kernel_diff = numpy.diag(standard_symmetric_noisy_kernel_matrix - standard_symm_kernel_matrix)
        self.assert_vector_within_relative(kernel_diff, noise, 1e-6)

  def test_kernel_gradient_tensor_evaluation(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      xn, d = x.shape
      zn, _ = z.shape
      full_zx = numpy.tile(z, (xn, 1))
      full_xz = numpy.reshape(numpy.tile(x, (1, zn)), (xn * zn, d))
      full_zz = numpy.tile(z, (zn, 1))
      full_zz_trans = numpy.reshape(numpy.tile(z, (1, zn)), (zn * zn, d))
      for covariance_object in self.differentiable_covariances:
        cov = covariance_object(hparams)
        standard_gtensor = cov.build_kernel_grad_tensor(z, x)
        basic_gtensor = cov.grad_covariance(full_xz, full_zx)
        standard_gtensor_flat = numpy.array([standard_gtensor[:, :, i].reshape(-1) for i in range(d)]).T
        self.assert_vector_within_relative_norm(
          standard_gtensor_flat,
          basic_gtensor,
          d * xn * zn * 1e-8,
        )
        standard_sgtensor = cov.build_kernel_grad_tensor(z)
        basic_sgtensor = cov.grad_covariance(full_zz_trans, full_zz)
        standard_sgtensor_flat = numpy.array([standard_sgtensor[:, :, i].reshape(-1) for i in range(d)]).T
        self.assert_vector_within_relative_norm(
          standard_sgtensor_flat,
          basic_sgtensor,
          d * zn * zn * 1e-8,
        )

  def test_kernel_hyperparameter_gradient_tensor_evaluation(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      xn, d = x.shape
      zn, _ = z.shape
      full_zx = numpy.tile(z, (xn, 1))
      full_xz = numpy.reshape(numpy.tile(x, (1, zn)), (xn * zn, d))
      full_zz = numpy.tile(z, (zn, 1))
      full_zz_trans = numpy.reshape(numpy.tile(z, (1, zn)), (zn * zn, d))
      for covariance_object in self.differentiable_covariances:
        cov = covariance_object(hparams)
        dh = cov.num_hyperparameters
        standard_hgtensor = cov.build_kernel_hparam_grad_tensor(z, x)
        basic_hgtensor = cov.hyperparameter_grad_covariance(full_xz, full_zx)
        standard_hgtensor_flat = numpy.array([standard_hgtensor[:, :, i].reshape(-1) for i in range(dh)]).T
        self.assert_vector_within_relative_norm(
          standard_hgtensor_flat,
          basic_hgtensor,
          dh * xn * zn * 1e-8,
        )
        standard_shgtensor = cov.build_kernel_hparam_grad_tensor(z)
        basic_shgtensor = cov.hyperparameter_grad_covariance(full_zz_trans, full_zz)
        standard_shgtensor_flat = numpy.array([standard_shgtensor[:, :, i].reshape(-1) for i in range(dh)]).T
        self.assert_vector_within_relative_norm(
          standard_shgtensor_flat,
          basic_shgtensor,
          dh * zn * zn * 1e-8,
        )

  def test_kernel_gradient_against_finite_difference(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      xn, d = x.shape
      zn, _ = z.shape
      n = min(xn, zn)
      for covariance_object in self.differentiable_covariances:
        cov = covariance_object(hparams)
        for i in range(n):
          func = lambda u: cov.covariance(u, numpy.reshape(z[i, :], (1, -1)))
          grad = lambda u: cov.grad_covariance(u, numpy.reshape(z[i, :], (1, -1)))
          h = 1e-8
          self.check_gradient_with_finite_difference(
            numpy.reshape(x[i, :], (1, -1)),
            func,
            grad,
            tol=d * 2e-6,
            fd_step=h * numpy.ones(d),
            use_complex=True,
          )

  def test_kernel_hyperparameter_gradient_against_finite_difference(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      xn, d = x.shape
      zn, _ = z.shape
      n = min(xn, zn)
      x = x[:n, :]
      z = z[:n, :]
      for covariance_object in self.differentiable_covariances:

        def func(hparams):
          cov = covariance_object(hparams.squeeze())
          return cov.covariance(x, z)

        def grad(hparams):
          cov = covariance_object(hparams.squeeze())
          return cov.hyperparameter_grad_covariance(x, z)

        self.check_gradient_with_finite_difference(
          numpy.reshape(hparams, (1, -1)),
          func,
          grad,
          tol=d * n * n * 1e-6,
          fd_step=1e-8 * hparams,
        )


class TestMultitaskCovariance(CovariancesTestBase):
  tasks = [0.1, 0.3, 1.0]

  def test_covariance_creation(self):
    with pytest.raises(AssertionError):
      MultitaskTensorCovariance([1.0, 1.2, 1.4], covariance.C0RadialMatern, covariance.C2RadialMatern)
    with pytest.raises(AssertionError):
      MultitaskTensorCovariance([1.0, 1.2], covariance.C2RadialMatern, covariance.C2RadialMatern)
    with pytest.raises(HyperparameterInvalidError):
      MultitaskTensorCovariance([1.0, 1.2, -1.4], covariance.C2RadialMatern, covariance.C2RadialMatern)
    with pytest.raises(HyperparameterInvalidError):
      MultitaskTensorCovariance([1.0, 1.2, numpy.nan], covariance.C2RadialMatern, covariance.C2RadialMatern)
    with pytest.raises(HyperparameterInvalidError):
      MultitaskTensorCovariance([1.0, 1.2, None], covariance.C2RadialMatern, covariance.C2RadialMatern)
    with pytest.raises(HyperparameterInvalidError):
      MultitaskTensorCovariance([1.0, 1.2, numpy.inf], covariance.C2RadialMatern, covariance.C2RadialMatern)

    cov = MultitaskTensorCovariance([2.3, 4.5, 6.7], covariance.SquareExponential, covariance.C2RadialMatern)
    assert numpy.all(cov.hyperparameters == [2.3, 4.5, 6.7])
    assert cov.process_variance == 2.3
    assert cov.dim == 2
    assert numpy.all(cov.physical_covariance.hyperparameters == [1.0, 4.5])
    assert cov.physical_covariance.process_variance == 1.0
    assert cov.physical_covariance.dim == 1
    assert numpy.all(cov.task_covariance.hyperparameters == [1.0, 6.7])
    assert cov.task_covariance.process_variance == 1.0
    assert cov.task_covariance.dim == 1

    cov.hyperparameters = [1.2, 3.4, 5.6, 7.8]
    assert numpy.all(cov.hyperparameters == [1.2, 3.4, 5.6, 7.8])
    assert cov.physical_covariance.dim == 2
    assert cov.task_covariance.dim == 1

  def test_covariance_symmetric(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      z_trunc = z[: len(x), :]
      x = numpy.concatenate((x, numpy.random.choice(self.tasks, size=(len(x), 1))), axis=1)
      z = numpy.concatenate((z_trunc, numpy.random.choice(self.tasks, size=(len(z_trunc), 1))), axis=1)
      for c1, c2 in itertools.product(self.differentiable_covariances, self.differentiable_covariances):
        hparams_with_task = numpy.append(hparams, numpy.random.random())
        cov = MultitaskTensorCovariance(hparams_with_task, c1, c2)
        kernel_at_xz = cov.covariance(x=x, z=z)
        kernel_at_zx = cov.covariance(x=z, z=x)
        self.assert_vector_within_relative(kernel_at_xz, kernel_at_zx, 1e-8)

  def test_kernel_matrix_evaluation(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      x = numpy.concatenate((x, numpy.random.choice(self.tasks, size=(len(x), 1))), axis=1)
      z = numpy.concatenate((z, numpy.random.choice(self.tasks, size=(len(z), 1))), axis=1)
      xn, d = x.shape
      zn, _ = z.shape
      full_zx = numpy.tile(z, (xn, 1))
      full_xz = numpy.reshape(numpy.tile(x, (1, zn)), (xn * zn, d))
      full_zz = numpy.tile(z, (zn, 1))
      full_zz_trans = numpy.reshape(numpy.tile(z, (1, zn)), (zn * zn, d))
      for c1, c2 in itertools.product(self.differentiable_covariances, self.differentiable_covariances):
        hparams_with_task = numpy.append(hparams, numpy.random.random())
        cov = MultitaskTensorCovariance(hparams_with_task, c1, c2)
        standard_kernel_matrix = cov.build_kernel_matrix(z, x)
        basic_kernel_matrix = cov.covariance(full_xz, full_zx)
        self.assert_vector_within_relative_norm(
          standard_kernel_matrix.reshape(-1),
          basic_kernel_matrix,
          xn * zn * 1e-8,
        )
        standard_symm_kernel_matrix = cov.build_kernel_matrix(z)
        basic_symm_kernel_matrix = cov.covariance(full_zz, full_zz_trans)
        self.assert_vector_within_relative_norm(
          standard_symm_kernel_matrix.reshape(-1),
          basic_symm_kernel_matrix,
          zn * zn * 1e-8,
        )
        noise = numpy.full(zn, numpy.random.random() * 1e-4)
        standard_symmetric_noisy_kernel_matrix = cov.build_kernel_matrix(z, noise_variance=noise)
        kernel_diff = numpy.diag(standard_symmetric_noisy_kernel_matrix - standard_symm_kernel_matrix)
        self.assert_vector_within_relative(kernel_diff, noise, 1e-6)

  def test_kernel_gradient_tensor_evaluation(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      x = numpy.concatenate((x, numpy.random.choice(self.tasks, size=(len(x), 1))), axis=1)
      z = numpy.concatenate((z, numpy.random.choice(self.tasks, size=(len(z), 1))), axis=1)
      xn, d = x.shape
      zn, _ = z.shape
      full_zx = numpy.tile(z, (xn, 1))
      full_xz = numpy.reshape(numpy.tile(x, (1, zn)), (xn * zn, d))
      full_zz = numpy.tile(z, (zn, 1))
      full_zz_trans = numpy.reshape(numpy.tile(z, (1, zn)), (zn * zn, d))
      for c1, c2 in itertools.product(self.differentiable_covariances, self.differentiable_covariances):
        hparams_with_task = numpy.append(hparams, numpy.random.random())
        cov = MultitaskTensorCovariance(hparams_with_task, c1, c2)
        standard_gtensor = cov.build_kernel_grad_tensor(z, x)
        basic_gtensor = cov.grad_covariance(full_xz, full_zx)
        standard_gtensor_flat = numpy.array([standard_gtensor[:, :, i].reshape(-1) for i in range(d)]).T
        self.assert_vector_within_relative_norm(
          standard_gtensor_flat,
          basic_gtensor,
          d * xn * zn * 1e-8,
        )
        standard_sgtensor = cov.build_kernel_grad_tensor(z)
        basic_sgtensor = cov.grad_covariance(full_zz_trans, full_zz)
        standard_sgtensor_flat = numpy.array([standard_sgtensor[:, :, i].reshape(-1) for i in range(d)]).T
        self.assert_vector_within_relative_norm(
          standard_sgtensor_flat,
          basic_sgtensor,
          d * zn * zn * 1e-8,
        )

  def test_kernel_gradient_against_finite_difference(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      x = numpy.concatenate((x, numpy.random.choice(self.tasks, size=(len(x), 1))), axis=1)
      z = numpy.concatenate((z, numpy.random.choice(self.tasks, size=(len(z), 1))), axis=1)
      xn, d = x.shape
      zn, _ = z.shape
      n = min(xn, zn)
      for c1, c2 in itertools.product(self.differentiable_covariances, self.differentiable_covariances):
        hparams_with_task = numpy.append(hparams, max(numpy.random.random(), TASK_LENGTH_LOWER_BOUND))
        cov = MultitaskTensorCovariance(hparams_with_task, c1, c2)
        for i in range(n):
          func = lambda u: cov.covariance(u, numpy.reshape(z[i, :], (1, -1)))
          grad = lambda u: cov.grad_covariance(u, numpy.reshape(z[i, :], (1, -1)))
          h = 1e-8
          self.check_gradient_with_finite_difference(
            numpy.reshape(x[i, :], (1, -1)),
            func,
            grad,
            tol=d * 1e-6,
            fd_step=h * numpy.ones(d),
            use_complex=True,
          )

  def test_kernel_hyperparameter_gradient_against_finite_difference(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      x = numpy.concatenate((x, numpy.random.choice(self.tasks, size=(len(x), 1))), axis=1)
      z = numpy.concatenate((z, numpy.random.choice(self.tasks, size=(len(z), 1))), axis=1)
      xn, d = x.shape
      zn, _ = z.shape
      n = min(xn, zn)
      x = x[:n, :]
      z = z[:n, :]
      for c1, c2 in itertools.product(self.differentiable_covariances, self.differentiable_covariances):
        hparams_with_task = numpy.append(hparams, numpy.random.random())

        def func(hparams):
          cov = MultitaskTensorCovariance(hparams.squeeze(), c1, c2)
          return cov.covariance(x, z)

        def grad(hparams):
          cov = MultitaskTensorCovariance(hparams.squeeze(), c1, c2)
          return cov.hyperparameter_grad_covariance(x, z)

        self.check_gradient_with_finite_difference(
          numpy.reshape(hparams_with_task, (1, -1)),
          func,
          grad,
          tol=d * n * n * 1e-6,
          fd_step=1e-8 * hparams_with_task,
        )

  def test_kernel_hyperparameter_gradient_tensor_evaluation(self):
    for x, z, hparams in zip(self.test_x, self.test_z, self.test_hparams):
      x = numpy.concatenate((x, numpy.random.choice(self.tasks, size=(len(x), 1))), axis=1)
      z = numpy.concatenate((z, numpy.random.choice(self.tasks, size=(len(z), 1))), axis=1)
      xn, d = x.shape
      zn, _ = z.shape
      full_zx = numpy.tile(z, (xn, 1))
      full_xz = numpy.reshape(numpy.tile(x, (1, zn)), (xn * zn, d))
      full_zz = numpy.tile(z, (zn, 1))
      full_zz_trans = numpy.reshape(numpy.tile(z, (1, zn)), (zn * zn, d))
      for c1, c2 in itertools.product(self.differentiable_covariances, self.differentiable_covariances):
        hparams_with_task = numpy.append(hparams, numpy.random.random())
        cov = MultitaskTensorCovariance(hparams_with_task, c1, c2)
        dh = cov.num_hyperparameters
        standard_hgtensor = cov.build_kernel_hparam_grad_tensor(z, x)
        basic_hgtensor = cov.hyperparameter_grad_covariance(full_xz, full_zx)
        standard_hgtensor_flat = numpy.array([standard_hgtensor[:, :, i].reshape(-1) for i in range(dh)]).T
        self.assert_vector_within_relative_norm(
          standard_hgtensor_flat,
          basic_hgtensor,
          dh * xn * zn * 1e-8,
        )
        standard_shgtensor = cov.build_kernel_hparam_grad_tensor(z)
        basic_shgtensor = cov.hyperparameter_grad_covariance(full_zz_trans, full_zz)
        standard_shgtensor_flat = numpy.array([standard_shgtensor[:, :, i].reshape(-1) for i in range(dh)]).T
        self.assert_vector_within_relative_norm(
          standard_shgtensor_flat,
          basic_shgtensor,
          dh * zn * zn * 1e-8,
        )


# NOTE: The min/max values are chosen to avoid overflow ... in reality _scale_difference_matrix is unneeded
@pytest.mark.parametrize("dim", [1, 3, 5])
@pytest.mark.parametrize("num_points", [1, 4, 10])
def test_scale_difference_matrix2(dim, num_points):
  def _generate_random_scale_and_difference_matrix(dim, num_points):
    scale = numpy.random.uniform(-1000, 1000, size=(num_points, num_points))
    difference_matrix = numpy.random.uniform(-1000, 1000, size=(num_points, num_points, dim))
    return scale, difference_matrix

  scale, difference_matrix = _generate_random_scale_and_difference_matrix(dim, num_points)
  # pylint: disable=protected-access
  scaled = covariance._scale_difference_matrix(scale, difference_matrix)
  # pylint: enable=protected-access
  for i in range(dim):
    numpy.testing.assert_array_equal(scaled[:, :, i], scale * difference_matrix[:, :, i])


class TestLinkers(object):
  """Tests that linkers contain all possible types defined in constants."""

  def test_covariance_links_have_all_covariance_types(self):
    """Test each covariance type is in a linker, and every linker key is a covariance type."""
    assert set(COVARIANCE_TYPES) == set(covariance.COVARIANCE_TYPES_TO_CLASSES.keys())
