# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest

from testaux.numerical_test_case import NumericalTestCase


class TestNumericalTestCase(NumericalTestCase):
  @pytest.mark.parametrize(
    "value,truth,tol,expected_to_pass",
    [
      (0.123456, 0.1234567, 1e-5, True),
      (0.123456, 0.1234567, 1e-6, False),
      (0.123456, -0.1234567, 1e-5, False),
      (1.23457e32, 1.23456e32, 1e-5, True),
      (1.23457e32, 1.23456e32, 1e-6, False),
      (1.23456e-8, 3.4567e-9, 1e-5, False),
      (1.23456e-10, 3.4567e-11, 1e-5, False),
      (1.23456e-12, 3.4567e-13, 1e-5, False),
      (1.23456e-18, 9.987321e-19, 1e-5, False),
      (1.23456e-22, 1.23456e-21, 1e-5, False),
      (1.0e36, 1.0e-12, 1e-5, False),
      (1.0e-20, 0, 1e-5, True),
      (0, 1.0e-20, 1e-5, False),
      (1.0e-10, 0, 1e-5, True),
      (0, 1.0e-10, 1e-5, False),
      (-1.0e-20, 1.0e-20, 1e-5, False),
      (2.34913897e16, 2.34913517e16, 1e-6, False),
      (2.34913897e-16, 2.34913517e-16, 1e-6, False),
      (-6.32175937e-08, -6.32173997e-08, 1e-6, False),
      (6.11198633e-07, 6.11197879e-07, 1e-6, False),
    ],
  )
  def test_assert_scalar_within_relative(self, value, truth, tol, expected_to_pass):
    if expected_to_pass:
      self.assert_scalar_within_relative(value, truth, tol)
    else:
      with pytest.raises(AssertionError):
        self.assert_scalar_within_relative(value, truth, tol)

  @pytest.mark.parametrize(
    "value,truth,tol,expected_to_pass",
    [
      (0.123456, 0.1234567, 1e-5, True),
      (0.123456, 0.1234567, 1e-6, False),
      (0.123456, -0.1234567, 1e-5, False),
      (1.23457e32, 1.23456e32, 1e-5, True),
      (1.23457e32, 1.23456e32, 1e-6, False),
      (1.23456e-9, 3.4567e-8, 1e-5, False),
      (1.23456e-9, 3.4567e-9, 1e-5, False),
      (1.23456e-10, 3.4567e-10, 1e-5, True),
      (1.23456e-18, 9.987321e-19, 1e-5, True),
      (1.23456e-22, 1.23456e-21, 1e-5, True),
      (1.0e36, 1.0e-12, 1e-5, False),
      (1.0e-20, 0, 1e-5, True),
      (0, 1.0e-20, 1e-5, True),
      (1.0e-8, 0, 1e-5, False),
      (0, 1.0e-8, 1e-5, False),
      (-1.0e-20, 1.0e-20, 1e-5, True),
      (2.34913897e16, 2.34913517e16, 1e-6, False),
      (2.34913897e-16, 2.34913517e-16, 1e-6, True),
      (-6.32175937e-08, -6.32173997e-08, 1e-6, True),
      (6.11198633e-07, 6.11197879e-07, 1e-6, True),
    ],
  )
  def test_assert_scalar_is_close(self, value, truth, tol, expected_to_pass):
    if expected_to_pass:
      self.assert_scalar_is_close(value, truth, tol)
    else:
      with pytest.raises(AssertionError):
        self.assert_scalar_is_close(value, truth, tol)

  @pytest.mark.parametrize(
    "value,truth,tol,expected_to_pass",
    [
      (0.123456, 0.1234567, 1e-5, True),
      (0.123456, 0.1234567, 1e-6, False),
      (0.123456, 0.0000001, 1e-5, False),
      (1.23457e32, 1.23456e32, 1e-5, True),
      (1.23457e32, 1.23456e32, 1e-6, False),
      (1.23456e-9, 3.4567e-8, 1e-5, False),
      (1.23456e-9, 3.4567e-9, 1e-5, False),
      (1.23456e-12, 3.4567e-13, 1e-5, True),
      (1.23456e-18, 9.987321e-19, 1e-5, True),
      (1.23456e-22, 1.23456e-21, 1e-5, True),
      (1.0e36, 1.0e-12, 1e-5, False),
      (1.0e-20, 0, 1e-5, True),
      (0, 1.0e-20, 1e-5, True),
      (1.0e-8, 0, 1e-5, False),
      (0, 1.0e-8, 1e-5, False),
      (-1.0e-20, 1.0e-20, 1e-5, True),
      (2.34913897e16, 2.34913517e16, 1e-6, False),
      (2.34913897e-16, 2.34913517e-16, 1e-6, True),
      (-6.32175937e-08, -6.32173997e-08, 1e-6, True),
      (6.11198633e-07, 6.11197879e-07, 1e-6, True),
    ],
  )
  def test_assert_vector_row_wise_norm_is_close(self, value, truth, tol, expected_to_pass):
    n = 12
    dim = 5
    random_vector = numpy.zeros((n, dim))
    index = numpy.random.choice(n)
    value_vector = numpy.copy(random_vector)
    truth_vector = numpy.copy(random_vector)
    value_vector[index, 0] = value
    truth_vector[index, 0] = truth
    if expected_to_pass:
      self.assert_vector_row_wise_norm_is_close(value_vector, truth_vector, tol, norm=1)
    else:
      with pytest.raises(AssertionError):
        self.assert_vector_row_wise_norm_is_close(value_vector, truth_vector, tol, norm=1)
