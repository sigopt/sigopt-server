# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest

from libsigopt.aux.samplers import *


class TestGridSampler(object):
  def test_grid_generation(self):
    domain_bounds = numpy.array([[0.0, 1.0], [-2.0, 3.0], [2.71, 3.14]])
    points_per_dimension = [7, 11, 8]

    # Test that all points are present
    grid = generate_grid_points(points_per_dimension, domain_bounds)

    per_axis_grid = [
      numpy.linspace(bounds[0], bounds[1], points_per_dimension[i]) for i, bounds in enumerate(domain_bounds)
    ]

    # Loop ordering assumes the output is ordered a certain way.
    for i, y_coord in enumerate(per_axis_grid[1]):
      for j, x_coord in enumerate(per_axis_grid[0]):
        for k, z_coord in enumerate(per_axis_grid[2]):
          truth = numpy.array([x_coord, y_coord, z_coord])
          index = i * per_axis_grid[2].size * per_axis_grid[0].size + j * per_axis_grid[2].size + k
          test = grid[index, ...]
          assert numpy.all(test == truth)

    # Also test that scalar points_per_dimension works
    points_per_dimension = [5, 5, 5]
    grid_truth = generate_grid_points(points_per_dimension, domain_bounds)

    points_per_dimension = 5
    grid_test = generate_grid_points(points_per_dimension, domain_bounds)

    assert numpy.all(grid_truth == grid_test)


class TestLatinHypercubeSampler(object):
  @pytest.mark.parametrize(
    "domain_bounds",
    [
      [[0.0, 0.0]],
      [[-1.0, 1.0]],
      [[-10.0, 10.0]],
      [[-500.0, -490.0]],
      [[6000.0, 6000.001]],
      [[-1.0, 1.0], [-1.0, 1.0]],
      [[-1.0, 1.0], [-1.0, 1.0], [-1.0, 1.0]],
      [[-7000.0, 10000.0], [-8000.0, -7999.0], [10000.06, 10000.0601]],
      [[-7000.0, 10000.0], [-8000.0, -8000.0], [10000.06, 10000.0601], [2.0, 2.0]],
    ],
  )
  @pytest.mark.parametrize("num_points", [1, 2, 5, 10, 20])
  def test_latin_hypercube_equally_spaced(self, domain_bounds, num_points):
    domain_bounds = numpy.asarray(domain_bounds)
    points = generate_latin_hypercube_points(num_points, domain_bounds)

    for point in points:
      assert numpy.all(point >= domain_bounds[:, 0]) and numpy.all(point <= domain_bounds[:, 1])

    untunable_indexes = [i for i, interval in enumerate(domain_bounds) if interval[0] == interval[1]]
    for index in untunable_indexes:
      assert points[-1][index] == domain_bounds[index][0]
      assert points[-1][index] == domain_bounds[index][1]

    for dim in range(len(domain_bounds)):
      # This size of each slice
      sub_domain_width = (domain_bounds[dim, 1] - domain_bounds[dim, 0]) / float(num_points)
      # Sort in dim dimension
      points = sorted(points, key=lambda points: points[dim])
      for i, point in enumerate(points):
        # This point must fall somewhere within the slice
        min_val = domain_bounds[dim, 0] + sub_domain_width * i
        max_val = min_val + sub_domain_width
        assert min_val <= point[dim] <= max_val


class TestRandomSampler(object):
  @pytest.mark.parametrize(
    "domain_bounds",
    [
      [[0.0, 0.0]],
      [[-1.0, 1.0]],
      [[-10.0, 10.0]],
      [[-500.0, -490.0]],
      [[6000.0, 6000.001]],
      [[-1.0, 1.0], [-1.0, 1.0]],
      [[-1.0, 1.0], [-1.0, 1.0], [-1.0, 1.0]],
      [[-7000.0, 10000.0], [-8000.0, -7999.0], [10000.06, 10000.0601]],
      [[-7000.0, 10000.0], [-8000.0, -8000.0], [10000.06, 10000.0601], [2.0, 2.0]],
    ],
  )
  @pytest.mark.parametrize("num_points", [1, 2, 5, 10, 20])
  @pytest.mark.parametrize(
    "random_generator",
    [
      generate_uniform_random_points,
      generate_halton_points,
      generate_sobol_points,
    ],
  )
  def test_random_points_within_domain(self, domain_bounds, num_points, random_generator):
    domain_bounds = numpy.asarray(domain_bounds)
    points = random_generator(num_points, domain_bounds)

    for point in points:
      assert numpy.all(point >= domain_bounds[:, 0]) and numpy.all(point <= domain_bounds[:, 1])

      untunable_indexes = [i for i, interval in enumerate(domain_bounds) if interval[0] == interval[1]]
      for index in untunable_indexes:
        assert points[-1][index] == domain_bounds[index][0]
        assert points[-1][index] == domain_bounds[index][1]


class TestConstrainedSamplers(object):
  halfspaces = numpy.array([[1, 1, -1e-5], [-1, -0, 0], [1, 0, -1e2], [-0, -1, 0], [0, 1, -1e2]])
  A = halfspaces[:, :-1]
  b = -halfspaces[:, -1]
  x0, _, _ = find_interior_point(halfspaces)
  domain_bounds = numpy.array([[0, 100] for _ in range(2)])

  def check_points_satisfy_constraints(self, samples):
    for s in samples:
      assert numpy.all(numpy.dot(self.A, s) <= self.b)

  def check_points_satisfy_domain_bounds(self, samples):
    for s in samples:
      assert numpy.all((s >= 0) & (s <= 100))

  def test_hitandrun_sampler(self):
    num_points = 100
    samples = generate_hitandrun_random_points(num_points, self.x0, self.A, self.b)
    assert samples.shape[0] == num_points
    self.check_points_satisfy_constraints(samples)
    self.check_points_satisfy_domain_bounds(samples)

  def test_rejection_with_padding_sampler(self):
    num_points = 100
    samples, success = generate_uniform_random_points_rejection_sampling_with_hitandrun_padding(
      num_points,
      self.domain_bounds,
      self.A,
      self.b,
      self.x0,
    )
    assert success is False
    assert samples.shape[0] == num_points
    self.check_points_satisfy_constraints(samples)
    self.check_points_satisfy_domain_bounds(samples)
