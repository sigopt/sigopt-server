# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import pytest

from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
)
from libsigopt.aux.geometry_utils import find_interior_point
from libsigopt.compute.domain import DEFAULT_NUM_RANDOM_NEIGHBORS, MAX_GRID_DIM, CategoricalDomain
from testaux.numerical_test_case import NumericalTestCase


def nd_simplex_halfspaces(dim):
  # return the halfspaces of an n-dim simplex, x_1 + x_2 + ..... x_n <= 1, x_i >= 0 and x_i <=1.
  n_halfspaces = 2 * dim + 1
  halfspaces = numpy.zeros((n_halfspaces, dim + 1))

  halfspaces[0, :-1] = 1
  halfspaces[0, -1] = -1

  for index in range(dim):
    imin = 1 + 2 * index
    imax = 1 + 2 * index + 1

    halfspaces[imin, -1] = 0
    halfspaces[imax, -1] = -1
    halfspaces[imin, index] = -1
    halfspaces[imax, index] = 1

  return halfspaces


class TestFindInteriorPoint(NumericalTestCase):
  def test_feasibly_constraint(self):
    dim = numpy.random.randint(2, 20)
    halfspaces = nd_simplex_halfspaces(dim)
    _, _, feasibility = find_interior_point(halfspaces)
    assert feasibility

  def test_infeasible_equality_constraint(self):
    dim = numpy.random.randint(2, 20)
    halfspaces = nd_simplex_halfspaces(dim)
    halfspaces = numpy.vstack((-halfspaces[0], halfspaces))
    _, _, feasibility = find_interior_point(halfspaces)
    assert not feasibility

  def test_infeasible_almost_equality_constraint(self):
    dim = numpy.random.randint(2, 20)
    halfspaces = nd_simplex_halfspaces(dim)
    halfspaces = numpy.vstack((-halfspaces[0], halfspaces))
    halfspaces[0, -1] -= 1e-8
    halfspaces[1, -1] -= 1e-8
    _, _, feasibility = find_interior_point(halfspaces)
    assert not feasibility

  def test_infeasible_constraint(self):
    dim = numpy.random.randint(2, 20)
    halfspaces = nd_simplex_halfspaces(dim)
    halfspaces = numpy.vstack((-halfspaces[0], halfspaces))
    halfspaces[0, -1] += 1
    halfspaces[1, -1] += 1
    _, _, feasibility = find_interior_point(halfspaces)
    assert not feasibility

  def test_chebyshev_center_hypercube(self):
    dim = numpy.random.randint(2, 40)
    halfspaces = nd_simplex_halfspaces(dim)
    halfspaces = halfspaces[1:]
    center, radius, feasibility = find_interior_point(halfspaces)
    assert feasibility
    self.assert_scalar_within_relative(radius, 0.5, 1e-8)
    self.assert_vector_within_relative(center, numpy.full_like(center, 0.5), 1e-8)

  def test_chebyshev_center_simplex(self):
    dim = numpy.random.randint(2, 40)
    halfspaces = nd_simplex_halfspaces(dim)
    center, radius, feasibility = find_interior_point(halfspaces)
    radius_exact = 1 / (numpy.sqrt(dim) * (numpy.sqrt(dim) + 1))
    assert feasibility
    self.assert_scalar_within_relative(radius, radius_exact, tol=1e-8)
    self.assert_vector_within_relative(center, numpy.full_like(center, radius_exact), 1e-8)

  def test_chebyshev_center_relaxed_hypercube(self):
    dim = numpy.random.randint(2, 40)
    halfspaces = nd_simplex_halfspaces(dim)
    halfspaces = halfspaces[1:]
    # relax the first bound to be [0, 2]
    halfspaces[1, :-1] = -2
    center, radius, feasibility = find_interior_point(halfspaces)
    assert feasibility
    self.assert_scalar_within_relative(radius, 0.5, tol=1e-8)
    self.assert_vector_within_relative(center[1:], numpy.full_like(center[1:], 0.5), 1e-8)


def map_one_hot_points_to_categorical_no_integer_snapping(domain, one_hot_points):
  unconstrained_domain_copy = CategoricalDomain(domain_components=domain.domain_components)
  return unconstrained_domain_copy.map_one_hot_points_to_categorical(one_hot_points)


class TestNeighborsFeasibility(object):
  def test_generate_neighboring_points_fails_unconstrained(self):

    # Fails with no constraints
    domain = CategoricalDomain(
      domain_components=[
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      ]
    )
    with pytest.raises(AssertionError):
      one_hot_point = numpy.array([0.5, 0.5, 0, 0, 0])
      domain.generate_integer_neighbors_for_integer_constraints(one_hot_point)

    # Fails with only double constraints
    domain = CategoricalDomain(
      domain_components=[
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      ],
      constraint_list=[
        {"weights": [0.0, 0.0, 0.2, 0.2, 0.0], "rhs": 1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    with pytest.raises(AssertionError):
      one_hot_point = numpy.array([0, 0, 0, 0, 0.5, 0.5, 0, 0, 0])
      domain.generate_integer_neighbors_for_integer_constraints(one_hot_point)

  def test_generate_neighboring_integers_points_exactly_test(self):
    domain = CategoricalDomain(
      domain_components=[
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      ],
      constraint_list=[
        {"weights": [0.2, 0.2, 0.0, 0, 0, 0], "rhs": 1, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.2, 0.2, 0, 0, 0], "rhs": 1, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, 1, 1, 0], "rhs": 1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      ],
    )

    n_neighbors = 2 ** len(domain.constrained_integer_indices)
    one_hot_point = numpy.array([1.1, 1.1, 1.1, 0, 0, 0, 0, 0])
    neighbors = domain.generate_integer_neighbors_for_integer_constraints(one_hot_point)
    assert neighbors.shape[0] == n_neighbors
    assert neighbors.shape[1] == domain.one_hot_dim
    true_neighbors = numpy.array(
      [
        [1, 1, 1, 0, 0, 0, 0, 0],
        [1, 1, 2, 0, 0, 0, 0, 0],
        [1, 2, 1, 0, 0, 0, 0, 0],
        [1, 2, 2, 0, 0, 0, 0, 0],
        [2, 1, 1, 0, 0, 0, 0, 0],
        [2, 1, 2, 0, 0, 0, 0, 0],
        [2, 2, 1, 0, 0, 0, 0, 0],
        [2, 2, 2, 0, 0, 0, 0, 0],
      ]
    )
    for true_neighbor in true_neighbors:
      assert true_neighbor in neighbors

  def test_generate_neighboring_integers_grid(self):
    d = numpy.random.randint(1, MAX_GRID_DIM)
    domain = CategoricalDomain(
      domain_components=[{"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [2, 3 + d]} for _ in range(d)],
      constraint_list=[
        {"weights": [0.5] * d, "rhs": 1, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    one_hot_point = numpy.array([2.5 + d for _ in range(d)])
    neighbors = domain.generate_integer_neighbors_for_integer_constraints(one_hot_point)
    assert neighbors.shape[0] == 2**d

  def test_generate_neighboring_integers_random(self):
    d = MAX_GRID_DIM + 1
    domain = CategoricalDomain(
      domain_components=[{"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]} for _ in range(d)],
      constraint_list=[
        {"weights": [1] * d, "rhs": d, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    one_hot_point = numpy.ones(d)
    neighbors = domain.generate_integer_neighbors_for_integer_constraints(one_hot_point)
    assert neighbors.shape[0] == DEFAULT_NUM_RANDOM_NEIGHBORS

  def test_snap_constrained_integer_points(self):
    domain = CategoricalDomain(
      domain_components=[
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      ],
      constraint_list=[
        {"weights": [0.25, 0.25, 0, 0, 0, 0, 0, 0, 0], "rhs": 2, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0.25, 0.25, 0, 0, 0, 0, 0, 0], "rhs": 2, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0, 0.25, 0, 0, 0, 0.25, 0, 0], "rhs": 2, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0, 0, 0, 0, 0, 0.25, 0.25, 0], "rhs": 2, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0, 0, 1.5, 1.5, 0, 0, 0, 0], "rhs": 2, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0, 0, 0, 1.5, 1.5, 0, 0, 0], "rhs": 2, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      ],
    )

    # A standard check to make sure we get three feasible integer neighbors from three points w/ feasible neighbors
    one_hot_next_points = numpy.array(
      [
        [4.1, 4.1, 4.1, 4.1, 4.1, 4.1, 4.1, 4.1, 1, 0, 0],
        [5.1, 5.1, 5.1, 5.1, 5.1, 5.1, 5.1, 5.1, 1, 0, 0],
        [6.1, 6.1, 6.1, 6.1, 6.1, 6.1, 6.1, 6.1, 1, 0, 0],
      ]
    )
    one_hot_points = domain.snap_one_hot_points_to_integer_feasible(one_hot_next_points)
    assert len(one_hot_points) == len(one_hot_next_points)
    for point in one_hot_points:
      assert domain.one_hot_domain.check_point_satisfies_constraints(point)
    categorical_points = map_one_hot_points_to_categorical_no_integer_snapping(domain, one_hot_points)
    for categorical_point in categorical_points:
      assert domain.check_point_satisfies_constraints(categorical_point)

    # One point has many feasible neighbors and the rest have none ... confirm that we get all feasible points
    one_hot_next_points = numpy.array(
      [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0],
        [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0],
        [1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0],
        [1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        [8, 8, 8, 8, 8, 8, 8, 8, 1, 0, 0],
      ]
    )
    one_hot_points = domain.snap_one_hot_points_to_integer_feasible(one_hot_next_points)
    assert len(one_hot_points) == len(one_hot_next_points)
    for point in one_hot_points:
      assert domain.one_hot_domain.check_point_satisfies_constraints(point)
    categorical_points = map_one_hot_points_to_categorical_no_integer_snapping(domain, one_hot_points)
    for categorical_point in categorical_points:
      assert domain.check_point_satisfies_constraints(categorical_point)

    # None of the points are feasible, in which case we ought to return an empty numpy aray
    one_hot_next_points = numpy.array(
      [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0],
        [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0],
        [1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0],
        [1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
      ]
    )
    one_hot_points = domain.snap_one_hot_points_to_integer_feasible(one_hot_next_points)
    for point in one_hot_points:
      assert not domain.one_hot_domain.check_point_satisfies_constraints(point)
    assert one_hot_points.size == 0

    # One next_point has two feasible neighbors and the other two one_hot_next_points have no feasible neighbors.
    # We ought to return only two feasible points, not three
    one_hot_next_points = numpy.array(
      [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        [2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0],
        [4.1, 4.1, 4.1, 4.1, 4.1, 4.1, 4.1, 4.1, 1, 0, 0],
      ]
    )
    domain_borderline = CategoricalDomain(
      domain_components=[
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      ],
      constraint_list=[
        {"weights": [0.25, 0.2, 0, 0, 0, 0, 0, 0, 0], "rhs": 2, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0.2, 0.2, 0, 0, 0, 0, 0, 0], "rhs": 2, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0, 0.2, 0, 0, 0, 0.2, 0, 0], "rhs": 2, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0, 0, 0, 0, 0, 0.2, 0.2, 0], "rhs": 2, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0, 0, 1.5, 1.5, 0, 0, 0, 0], "rhs": 2, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0, 0, 0, 0, 1.5, 1.5, 0, 0, 0], "rhs": 2, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    one_hot_points = domain_borderline.snap_one_hot_points_to_integer_feasible(one_hot_next_points)
    assert len(one_hot_points) == 2
    for point in one_hot_points:
      assert domain_borderline.one_hot_domain.check_point_satisfies_constraints(point)
    categorical_points = map_one_hot_points_to_categorical_no_integer_snapping(domain, one_hot_points)
    for categorical_point in categorical_points:
      assert domain.check_point_satisfies_constraints(categorical_point)

    # test snap one hot using random instead of grid
    d = MAX_GRID_DIM + 1
    domain = CategoricalDomain(
      domain_components=[{"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [1, 10]} for _ in range(d)],
      constraint_list=[
        {"weights": [1] * d, "rhs": d, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    one_hot_next_points = numpy.array(
      [
        [0.1] * d,
        [1.1] * d,
        [2.2] * d,
        [3.3] * d,
      ]
    )
    one_hot_points = domain.snap_one_hot_points_to_integer_feasible(one_hot_next_points)
    assert len(one_hot_points) == len(one_hot_next_points)
    for point in one_hot_points:
      assert domain.one_hot_domain.check_point_satisfies_constraints(point)
    categorical_points = map_one_hot_points_to_categorical_no_integer_snapping(domain, one_hot_points)
    for categorical_point in categorical_points:
      assert domain.check_point_satisfies_constraints(categorical_point)
