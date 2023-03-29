# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy

import numpy
import pytest
from flaky import flaky
from scipy.stats import beta, kstest, truncnorm

from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  QUANTIZED_EXPERIMENT_PARAMETER_NAME,
  ParameterPriorNames,
)
from libsigopt.aux.geometry_utils import find_interior_point
from libsigopt.compute.domain import CategoricalDomain, ContinuousDomain, FixedIndicesOnContinuousDomain
from testaux.utils import form_random_constrained_categorical_domain, form_random_unconstrained_categorical_domain


def domains_approximately_equal(domain1, domain2, inequality_tolerance=1e-14):
  assert isinstance(domain1, CategoricalDomain) and isinstance(domain2, CategoricalDomain)

  # Content can go from being a list to numpy, so this can fail ... if it does, what happens below will work
  try:
    same = (
      domain1.domain_components == domain2.domain_components
      and domain1.constraint_list == domain2.constraint_list
      and domain1.priors == domain2.priors
    )
  except ValueError:
    pass
  else:
    if same:
      return True

  if domain1.dim != domain2.dim:
    return False

  if domain1.one_hot_domain.force_hitandrun_sampling != domain2.one_hot_domain.force_hitandrun_sampling:
    return False

  if len(domain1.constraint_list) != len(domain2.constraint_list):
    return False

  for our_prior, their_prior in zip(domain1.priors, domain2.priors):
    if our_prior["name"] != their_prior["name"]:
      return False
    if our_prior["params"].keys() != their_prior["params"].keys():
      return False
    for key1, key2 in zip(our_prior["params"].keys(), their_prior["params"].keys()):
      if not numpy.isclose(our_prior["params"][key1], their_prior["params"][key2]):
        return False

  for our_dc, their_dc in zip(domain1.domain_components, domain2.domain_components):
    if our_dc["var_type"] != their_dc["var_type"] or len(our_dc["elements"]) != len(their_dc["elements"]):
      return False
    for our_element, their_element in zip(our_dc["elements"], their_dc["elements"]):
      if abs(our_element - their_element) > inequality_tolerance:  # Any sort of number near machine precision
        return False

  for our_cl, their_cl in zip(domain1.constraint_list, domain2.constraint_list):
    if abs(our_cl["rhs"] - their_cl["rhs"]) > inequality_tolerance:
      return False
    if our_cl["var_type"] != their_cl["var_type"]:
      return False
    for our_weight, their_weight in zip(our_cl["weights"], their_cl["weights"]):
      if abs(our_weight - their_weight) > inequality_tolerance:
        return False
  return True


def samples_satisfy_kolmogorov_smirnov_test(samples, domain_component, prior):
  if prior["name"] == ParameterPriorNames.NORMAL:
    loc = prior["params"]["mean"]
    scale = prior["params"]["scale"]
    a = (domain_component["elements"][0] - loc) / scale
    b = (domain_component["elements"][1] - loc) / scale
    cdf = lambda x: truncnorm.cdf(x, a, b, loc=loc, scale=scale)
  elif prior["name"] == ParameterPriorNames.BETA:
    loc = domain_component["elements"][0]
    scale = domain_component["elements"][1] - domain_component["elements"][0]
    shape_a = prior["params"]["shape_a"]
    shape_b = prior["params"]["shape_b"]
    cdf = lambda x: beta.cdf(x, shape_a, shape_b, loc=loc, scale=scale)
  else:
    raise ValueError("Prior is neither a normal nor beta distribution")

  _, p_value = kstest(samples, cdf)
  if p_value <= 0.005:
    return False
  else:
    return True


class TestContinuousDomain(object):
  def test_basics(self):
    domain = ContinuousDomain([[0, 1], [-2, 3]])
    assert all(m == 0.5 for m in domain.midpoint)
    assert domain.dim == 2
    assert domain.check_point_acceptable([0.3, 0.7])
    assert not domain.check_point_acceptable([-0.3, 0.7])
    assert domain.check_point_on_boundary([0, -2])
    assert not domain.check_point_on_boundary([1e-3, -2 + 1e-3])
    assert domain.check_point_on_boundary([1e-3, -2 + 1e-3], tol=1e-2)
    assert not domain.is_constrained
    assert numpy.all(domain.get_lower_upper_bounds() == numpy.array([[0, -2], [1, 3]]))

  # NOTE: other_domain is hard-coded outside domain by looking at form_random_domain
  def test_point_generation(self):
    dim = numpy.random.randint(2, 6)
    domain = form_random_unconstrained_categorical_domain(dim, categoricals_allowed=False).one_hot_domain
    num_points = numpy.random.randint(10, 1000)
    random_points = domain.generate_quasi_random_points_in_domain(num_points)
    assert tuple(random_points.shape) == (num_points, domain.dim)
    assert all(domain.check_point_acceptable(p) for p in random_points)
    assert tuple(domain.generate_grid_points_in_domain(6).shape) == (6**domain.dim, domain.dim)
    other_domain = ContinuousDomain([[20000, 30000]] * domain.dim)
    outside_points = other_domain.generate_quasi_random_points_in_domain(num_points)
    assert all(not domain.check_point_acceptable(p) for p in outside_points)
    assert all(domain.check_point_on_boundary(p) for p in domain.restrict_points_to_domain(outside_points))
    inner_points = domain.generate_random_points_near_point(num_points, domain.midpoint, numpy.random.gamma(1, 1))
    assert all(domain.check_point_acceptable(p) for p in inner_points)

  def test_constraints(self):
    num_points = 1000
    domain = ContinuousDomain([[0, 1], [-2, 3], [-1, 2]])
    constraint_list = [
      {
        "weights": numpy.array([1, 0, 1]),
        "rhs": 1,
      }
    ]
    domain_with_constraints = ContinuousDomain(domain.domain_bounds)
    domain_with_constraints.set_constraint_list(constraint_list=constraint_list)

    unconstrained_points = domain.generate_quasi_random_points_in_domain(num_points)
    unconstrained_points[-1, :] = [0, 0, 0]  # Does not satisfy the constraints
    constrained_points = domain_with_constraints.generate_quasi_random_points_in_domain(num_points)
    assert not all(unconstrained_points[:, 0] + unconstrained_points[:, 2] > 1)
    assert all(constrained_points[:, 0] + constrained_points[:, 2] > 1)
    assert all(domain_with_constraints.check_point_satisfies_constraints(p) for p in constrained_points)
    assert all(
      domain_with_constraints.check_point_satisfies_constraints(p) == (p[0] + p[2] > 1) for p in unconstrained_points
    )

    for p in unconstrained_points:
      if not domain_with_constraints.check_point_satisfies_constraints(p):
        assert domain_with_constraints.check_point_inside(p)
    assert all(domain_with_constraints.check_point_acceptable(p) for p in constrained_points)
    assert not all(domain_with_constraints.check_point_acceptable(p) for p in unconstrained_points)
    assert not domain.get_constraints_for_scipy()
    scipy_constraints = domain_with_constraints.get_constraints_for_scipy()
    for sc, cons in zip(scipy_constraints, constraint_list):
      assert sc["type"] == "ineq"
      assert numpy.all(sc["fun"](constrained_points) >= 0)
      assert numpy.all(sc["jac"](0) == cons["weights"])

    infeasible_constraint_list = [
      {
        "weights": numpy.array([1, 0, 1]),
        "rhs": 6,
      }
    ]
    with pytest.raises(AssertionError):
      domain_with_constraints.set_constraint_list(constraint_list=infeasible_constraint_list)

  def test_restrict_points_to_domain(self):
    num_points = 1000
    domain = ContinuousDomain([[0, 1], [-2, 3], [-1, 2]])
    constraint_list = [
      {
        "weights": numpy.array([1, 0, 1]),
        "rhs": 1,
      }
    ]
    domain_with_constraints = ContinuousDomain(domain.domain_bounds)
    domain_with_constraints.set_constraint_list(constraint_list=constraint_list)

    unconstrained_points = domain.generate_quasi_random_points_in_domain(num_points)
    unconstrained_points[-1, :] = [0, 0, 0]  # Does not satisfy the constraints
    constrained_points = domain_with_constraints.restrict_points_to_domain(unconstrained_points)
    assert not numpy.allclose(unconstrained_points, constrained_points)
    assert not all(unconstrained_points[:, 0] + unconstrained_points[:, 2] > 1)
    assert all(constrained_points[:, 0] + constrained_points[:, 2] > 1)
    assert all(domain_with_constraints.check_point_satisfies_constraints(p) for p in constrained_points)
    assert all(
      domain_with_constraints.check_point_satisfies_constraints(p) == (p[0] + p[2] > 1) for p in unconstrained_points
    )

    constrained_points_on = domain_with_constraints.restrict_points_to_domain(
      unconstrained_points,
      on_constraint=True,
    )
    assert not numpy.allclose(unconstrained_points, constrained_points_on)
    on_constraint = constrained_points_on[:, 0] + constrained_points_on[:, 2] < 1
    assert numpy.allclose(
      constrained_points_on[on_constraint, 0] + constrained_points_on[on_constraint, 2],
      1,
    )

  def test_restrict_points_to_domain_near_boundary(self):
    coeff_vector = [-1, 1]
    rhs = -0.0
    domain = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 100]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 100]},
      ],
      constraint_list=[
        {"weights": coeff_vector, "rhs": rhs, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      ],
    )

    viable_point = numpy.array([49.5040619673 - 1e-14, 49.5040619673])
    assert domain.one_hot_domain.check_point_acceptable(viable_point)
    assert not domain.one_hot_domain.check_point_on_boundary(viable_point)
    assert domain.one_hot_domain.check_point_on_boundary(viable_point, 1e-10)

    violate_point = numpy.array([99.0, 2.0])
    restricted_point = domain.one_hot_domain.restrict_points_to_domain(numpy.atleast_2d(violate_point))
    assert domain.one_hot_domain.check_point_acceptable(restricted_point[0])

  def test_restrict_points_to_domain_multiple_constraints(self):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 5]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3, 1]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [3, 8]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 3]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [-0.2, -0.1, 1, 2.5, 10]},
    ]
    constraint_list = [
      {"weights": [1, 1, 0, 0, 0, 0, 0], "rhs": 1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      {"weights": [1, 1, 1, 0, 0, 0, 0], "rhs": 2, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      {"weights": [0, 0, 0, 1, 1, 0, 0], "rhs": 2, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
    ]
    domain = CategoricalDomain(domain_components, constraint_list)
    one_hot_domain = domain.one_hot_domain
    one_hot_points = one_hot_domain.generate_quasi_random_points_in_domain(5)

    # Do not satisfy the constraints
    one_hot_points[-2, [0, 1, 2]] = [0.5, -1, -2]
    one_hot_points[-1, [0, 1, 2]] = [0, 0, 0]
    assert all(one_hot_domain.check_point_acceptable(p) for p in one_hot_points) is False

    restricted_points = one_hot_domain.restrict_points_to_domain(one_hot_points)
    assert not numpy.allclose(one_hot_points, restricted_points)
    assert all(one_hot_domain.check_point_acceptable(p) for p in restricted_points)

  @pytest.mark.parametrize("on_constraint", [True, False])
  def test_restrict_points_to_domain_edges(self, on_constraint):
    num_points = 1000
    dim = 6
    tolerance = 1e-12
    larger_domain = ContinuousDomain([[-1.2, 1.2]] * dim)
    domain = CategoricalDomain(
      domain_components=[{"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1]}] * dim,
      constraint_list=[
        {"weights": [1.0] * dim, "rhs": -1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    domain = domain.one_hot_domain

    unconstrained_points = larger_domain.generate_quasi_random_points_in_domain(num_points)
    unconstrained_points[-1, :] = [0] * dim  # Does not satisfy the constraints

    # viable point is outside the domain
    constrained_points = domain.restrict_points_to_domain(
      unconstrained_points,
      viable_point=larger_domain.midpoint,
      on_constraint=on_constraint,
    )
    assert not numpy.allclose(unconstrained_points, constrained_points)
    assert all(domain.check_point_satisfies_constraints(p) for p in constrained_points)
    assert all(sum(p) <= dim for p in constrained_points)

    # make viable points some corners of the domain
    edge_points = numpy.eye(dim)
    for viable_point in edge_points:
      constrained_points = domain.restrict_points_to_domain(
        unconstrained_points,
        viable_point=viable_point,
        on_constraint=on_constraint,
      )
      assert not numpy.allclose(unconstrained_points, constrained_points)
      assert all(
        domain.check_point_on_boundary(p, tolerance) for p in constrained_points if not domain.check_point_acceptable(p)
      )
      assert all(sum(p) <= (dim + tolerance) for p in constrained_points)

  @pytest.mark.parametrize("on_constraint", [True, False])
  @pytest.mark.parametrize("point", [None, [0.5, 0, 0], [0.5, 0.5, 0.5]])
  def test_generate_random_points_near_point_with_constraints(self, on_constraint, point):
    num_points = 1000
    domain = ContinuousDomain([[0, 1], [-2, 3], [-1, 2]])
    constraint_list = [
      {
        "weights": numpy.array([1, 0, 1]),
        "rhs": 1,
      }
    ]
    domain_with_constraints = ContinuousDomain(domain.domain_bounds)
    domain_with_constraints.set_constraint_list(constraint_list=constraint_list)

    if point is None:
      halfspaces = domain_with_constraints.convert_func_list_to_halfspaces()
      (
        point,
        _,
        _,
      ) = find_interior_point(halfspaces)
    else:
      point = numpy.array(point)

    inner_points = domain_with_constraints.generate_random_points_near_point(
      num_points,
      point,
      numpy.random.gamma(1, 1),
      on_constraint=on_constraint,
    )
    if on_constraint:
      assert numpy.all(inner_points[:, 0] + inner_points[:, 2] >= 1 - 1e8)
    else:
      assert all(domain_with_constraints.check_point_acceptable(p) for p in inner_points)

  @pytest.mark.parametrize("on_constraint", [True, False])
  def test_generate_points_near_domain_edges(self, on_constraint):
    num_points = 1000
    dim = 8
    tolerance = 1e-12
    std_dev = 0.1
    domain = CategoricalDomain(
      domain_components=[{"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1]}] * dim,
      constraint_list=[
        {"weights": [1.0] * dim, "rhs": 1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    domain = domain.one_hot_domain
    # viable points are the corners of the domain
    midpoint = numpy.atleast_2d(domain.midpoint)
    corners = numpy.eye(dim)
    edge_points = numpy.concatenate((midpoint, corners), axis=0)
    for point in edge_points:
      random_near_points = domain.generate_random_points_near_point(
        num_points, point, std_dev, on_constraint=on_constraint
      )
      assert all(
        domain.check_point_on_boundary(p, tolerance) for p in random_near_points if not domain.check_point_acceptable(p)
      )
      assert all(sum(p) >= (1 - tolerance) for p in random_near_points)


class TestCategoricalDomain(object):
  def test_basics(self):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [3, 8]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [-3, 3, 7]},
      {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [-0.1, 0.2, 2]},
    ]
    domain = CategoricalDomain(domain_components)

    assert domain.dim == 4
    assert domain.check_point_acceptable([0.3, 4, 3, 0.2])
    assert not domain.check_point_acceptable([0.3, 9, 3, -0.1])
    assert not domain.check_point_acceptable([0.3, 5, 5, 2])
    assert not domain.check_point_acceptable([0.3, 5, 3, 2.2])
    assert not domain.is_discrete
    assert domain.has_categoricals
    assert domain.has_quantized

    one_hot_domain_bounds = numpy.array(
      [
        [0, 2],
        [3, 8],
        [0, 1],
        [0, 1],
        [0, 1],
        [-0.1, 2],
      ]
    )
    assert domain.one_hot_dim == 6
    assert numpy.all(one_hot_domain_bounds == domain.one_hot_domain.domain_bounds)

    # Cannot consider a non-integer point for an integer dimension
    with pytest.raises(AssertionError):
      assert domain.check_point_acceptable([0.3, 4.5, 3, 0.2])

    assert domain.identify_unique_points(numpy.array([[1, 3, 3, 2], [1, 3, 3, 2]])).shape == (1, 4)
    assert domain.identify_unique_points(numpy.array([[1, 3, 3, -0.1], [1 + 1e-3, 3, 3, -0.1]])).shape == (2, 4)
    assert domain.identify_unique_points(
      numpy.array([[1, 3, 3, 0.2], [1 + 1e-3, 3, 3, 0.2]]), tolerance=1e-2
    ).shape == (1, 4)

    reference_points = numpy.array([[1, 3, 3, 0.2], [1.1, 4, 7, 2]])
    test_points = numpy.array([[1, 3, 3, 0.2]])
    assert domain.identify_unique_points(test_points, reference_points).shape == (0, 4)
    test_points = numpy.array([[1 + 1e-3, 3, 3, 0.2]])
    assert domain.identify_unique_points(test_points, reference_points).shape == (1, 4)
    test_points = numpy.array([[1 + 1e-3, 3, 3, 0.2]])
    assert domain.identify_unique_points(test_points, reference_points, tolerance=1e-2).shape == (0, 4)

  def test_domain_equality(self):
    domain = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3.3, 6.1]},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.1, 0.2, 2.6, 10e3]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
      ],
      constraint_list=[
        {"weights": [1.0, 0.0, -0.5, 0.0, 2.2, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [1.0, 0.0, -0.5, 0.0, 0.0, 0.0, 0.0], "rhs": 1.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 1.0], "rhs": 1.0, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    assert domains_approximately_equal(domain, domain)

    other_domain = copy.deepcopy(domain)
    del other_domain.constraint_list[0]
    assert not domains_approximately_equal(domain, other_domain)

    other_domain = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.4]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3.3, 6.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
      ],
      constraint_list=[
        {"weights": [1.0, 0.0, -0.5, 0.0, 2.2, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [1.0, 0.0, -0.5, 0.0, 0.0, 0.0], "rhs": 1.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, -1.0, 0.0, 1.0], "rhs": 1.0, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    assert not domains_approximately_equal(domain, other_domain)

    other_domain = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2, 1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3.3, 6.1]},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.1, 0.2, 2.6, 10e3]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
      ],
      constraint_list=[
        {"weights": [1.0, 0.0, -0.5, 0.0, 2.2, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [1.0, 0.0, -0.5, 0.0, 0.0, 0.0, 0.0], "rhs": 1.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 1.0], "rhs": 1.0, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    assert not domains_approximately_equal(domain, other_domain)

    other_domain = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3.3, 6.1]},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.1, 2.6, 0.2, 10e3]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
      ],
      constraint_list=[
        {"weights": [1.0, 0.0, -0.5, 0.0, 2.2, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [1.0, 0.0, -0.5, 0.0, 0.0, 0.0, 0.0], "rhs": 1.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 1.0], "rhs": 1.0, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    assert not domains_approximately_equal(domain, other_domain)

    other_domain = CategoricalDomain(
      domain_components=[
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3.3, 6.1]},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.1, 0.2, 2.6, 10e3]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
      ],
      constraint_list=[
        {"weights": [0.0, 1.0, -0.5, 0.0, 2.2, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 1.0, -0.5, 0.0, 0.0, 0.0, 0.0], "rhs": 1.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 1.0], "rhs": 1.0, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    assert not domains_approximately_equal(domain, other_domain)

    other_domain = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3.3, 6.1]},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.1, 0.2, 2.6, 10e3]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
      ],
      constraint_list=[
        {"weights": [1.0, 0.0, -0.5, 0.0, 2.2, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [1.0, 0.0, -0.5, 0.0, 0.0, 0.0, 0.0], "rhs": 1.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 1.0], "rhs": 1.0, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    assert not domains_approximately_equal(domain, other_domain)

    other_domain = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3.3, 6.1]},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.1, 0.2, 2.6, 10e3]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
      ],
      constraint_list=[
        {"weights": [1.0, 0.0, -0.4, 0.0, 2.2, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [1.0, 0.0, -0.5, 0.0, 0.0, 0.0, 0.0], "rhs": 1.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 1.0], "rhs": 1.0, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    assert not domains_approximately_equal(domain, other_domain)

    other_domain = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3.3, 6.1]},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.1, 0.2, 2.6, 10e3]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
      ],
      constraint_list=[
        {"weights": [1.0, 0.0, -0.5, 0.0, 2.2, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [1.0, 0.0, -0.5, 0.0, 0.0, 0.0, 0.0], "rhs": 1.2, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {"weights": [0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 1.0], "rhs": 1.0, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    assert not domains_approximately_equal(domain, other_domain)

    # This domain is considered similar enough to be equal
    other_domain = CategoricalDomain(
      domain_components=[
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3.3]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1, 2]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 1.1]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3.3, 6.1]},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.1, 0.2, 2.6, 10e3]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 5]},
      ],
      constraint_list=[
        {"weights": [1.0, 0.0, -0.5, 0.0, 2.2, 0.0, 0.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        {
          "weights": [1.0, 0.0, -0.5, 0.0, 0.0, 0.0, 0.0],
          "rhs": 1.3 + 1e-15,
          "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME,
        },
        {"weights": [0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 1.0], "rhs": 1.0, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      ],
    )
    assert domains_approximately_equal(domain, other_domain)

  def test_reset_constraint_list(self):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
    ]
    constraint_list = [
      {"weights": [-1, -1, -1], "rhs": -10, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
    ]
    domain = CategoricalDomain(domain_components, constraint_list=constraint_list)
    domain.one_hot_domain.set_constraint_list([])
    assert domain.one_hot_domain.one_hot_halfspaces is None
    assert domain.one_hot_domain.one_hot_unconstrained_indices == list(range(3))

  def test_quantized_domain(self):
    inf_quantized_comp = {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [-0.2, 0.2, numpy.inf]}
    with pytest.raises(AssertionError):
      assert CategoricalDomain(domain_components=[inf_quantized_comp])

    same_quantized_comp = {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.2, 0.2]}
    with pytest.raises(AssertionError):
      assert CategoricalDomain(domain_components=[same_quantized_comp])

    one_quantized_comp = {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.2]}
    with pytest.raises(AssertionError):
      assert CategoricalDomain(domain_components=[one_quantized_comp])

    domain = CategoricalDomain(
      domain_components=[
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.1, 0.2, 26, 1e3]},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.31, 0, -2, -5]},
      ]
    )

    one_hot_points = numpy.array(
      [
        [0.1, -5],
        [1000, 0],
        [1024, 0],
        [0.15, -2.5],
        [23, 0.16],
        [999, -8],
      ]
    )

    quantized_points = numpy.array(
      [
        [0.1, -5],
        [1000, 0],
        [1000, 0],
        [0.1, -2],
        [26, 0.31],
        [1000, -5],
      ]
    )

    assert numpy.all(domain.round_one_hot_points_quantized_values(one_hot_points) == quantized_points)
    assert numpy.all(domain.map_one_hot_points_to_categorical(one_hot_points) == quantized_points)
    assert numpy.all(domain.map_categorical_point_to_one_hot(one_hot_points) == one_hot_points)

  def test_quantized_unique(self):
    domain = CategoricalDomain(
      [{"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1e-5, 1.1e-5, 1.11e-5, 1.111e-5, 1]}]
    )
    points = numpy.array([[1e-5], [1.1e-5], [1.11e-5], [1.111e-5]])
    unique_points = domain.identify_unique_points(points)
    assert len(unique_points) == 4
    assert numpy.all(points == unique_points)

    unique_points = domain.identify_unique_points(points, tolerance=1e-5)
    assert len(unique_points) == 1
    assert numpy.all(points[0] == unique_points)

    unique_points = domain.identify_unique_points(points, tolerance=1e-7)
    assert len(unique_points) == 3
    assert numpy.all(points[:3] == unique_points)

    domain = CategoricalDomain(
      [{"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1e-5, 1.1e-5, 1.11e-5, 1.111e-5, 1e-4]}]
    )
    unique_points = domain.identify_unique_points(points)
    assert len(unique_points) == 4
    assert numpy.all(points == unique_points)

    unique_points = domain.identify_unique_points(points, tolerance=1e-4)
    assert len(unique_points) == 1
    assert numpy.all(points[0] == unique_points)

    unique_points = domain.identify_unique_points(points, tolerance=1e-5)
    assert len(unique_points) == 3
    assert numpy.all(points[:3] == unique_points)

  def test_unconstrained_point_generation(self):
    domain = form_random_unconstrained_categorical_domain(numpy.random.randint(2, 10))
    num_points = numpy.random.randint(50, 150)

    points = domain.generate_quasi_random_points_in_domain(num_points)
    assert tuple(points.shape) == (num_points, domain.dim)
    assert all(domain.check_point_acceptable(point) for point in points)
    one_hot_points = numpy.array([domain.map_categorical_point_to_one_hot(p) for p in points])
    remapped_categorical_points = domain.map_one_hot_points_to_categorical(one_hot_points, temperature=1e-2)
    assert numpy.all(points == remapped_categorical_points)

    one_hot_points = domain.one_hot_domain.generate_quasi_random_points_in_domain(num_points)
    categorical_points = domain.map_one_hot_points_to_categorical(one_hot_points, temperature=1e-2)
    remapped_one_hot_points = numpy.array([domain.map_categorical_point_to_one_hot(p) for p in categorical_points])
    for mapping in domain.one_hot_to_categorical_mapping:
      if mapping["var_type"] == DOUBLE_EXPERIMENT_PARAMETER_NAME:
        assert numpy.all(one_hot_points[:, mapping["input_ind"]] == remapped_one_hot_points[:, mapping["input_ind"]])

  def test_constrained_point_generation(self):
    domain = form_random_constrained_categorical_domain(
      n_double_param=5, n_int_param=5, n_cat_param=1, n_quantized_param=1
    )
    num_points = numpy.random.randint(50, 150)

    # Check points in categorical domain
    categorical_points = domain.generate_quasi_random_points_in_domain(num_points)
    assert tuple(categorical_points.shape) == (num_points, domain.dim)
    assert all(domain.check_point_acceptable(point) for point in categorical_points)

    # Check points in one_hot domain
    one_hot_points = domain.one_hot_domain.generate_quasi_random_points_in_domain(num_points)
    assert tuple(one_hot_points.shape) == (num_points, domain.one_hot_dim)
    assert all(domain.one_hot_domain.check_point_inside(point) for point in one_hot_points)
    assert all(domain.one_hot_domain.check_point_satisfies_constraints(point) for point in one_hot_points)

  def test_integer_constraint_samples_satisfy_equality(self):
    # Check ability to return points that satisfy not just strict less than inequality but also equality
    domain_components = [
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
    ]
    less_than_constraints = [
      {"weights": [-1, -1], "rhs": -10, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
    ]
    domain = CategoricalDomain(domain_components, less_than_constraints)
    categorical_points = domain.generate_quasi_random_points_in_domain(100)
    constraint_values = numpy.sum(categorical_points, axis=1)
    assert 10 in constraint_values

    # Check ability to return points that satisfy not just strict greater than inequality but also equality
    greater_than_constraints = [
      {"weights": [1, 1], "rhs": 10, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
    ]
    domain = CategoricalDomain(domain_components, greater_than_constraints)
    categorical_points = domain.generate_quasi_random_points_in_domain(100)
    constraint_values = numpy.sum(categorical_points, axis=1)
    assert 10 in constraint_values

  def test_round_one_hot_points(self):
    all_cats = [1, 2, 6, 9]
    domain = CategoricalDomain(
      [
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [1, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-11.1, 4.234]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": all_cats},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [1.0, 2.0, 5.3]},
      ]
    )

    one_hot_points = numpy.array(
      [
        [4.8, 0.8, 0.9, 0.9, 0.5, 0.6, 0.5],
        [3.3, 2.3, 0.2, 0.4, 0.6, 0.8, 4.1],
      ]
    )
    int_rounded_answers = numpy.array(
      [
        [5.0, 0.8, 0.9, 0.9, 0.5, 0.6, 0.5],
        [3.0, 2.3, 0.2, 0.4, 0.6, 0.8, 4.1],
      ]
    )
    int_rounded_points = domain.round_one_hot_points_integer_values(one_hot_points)
    assert numpy.all(int_rounded_points == int_rounded_answers)

    cat_rounded_answers = numpy.array(
      [
        [4.8, 0.8, 1.0, 0.0, 0.0, 0.0, 0.5],
        [3.3, 2.3, 0.0, 0.0, 0.0, 1.0, 4.1],
      ]
    )
    cat_rounded_points = domain.round_one_hot_points_categorical_values(one_hot_points)
    assert numpy.all(cat_rounded_points == cat_rounded_answers)

    quant_rounded_answers = numpy.array(
      [
        [4.8, 0.8, 0.9, 0.9, 0.5, 0.6, 1.0],
        [3.3, 2.3, 0.2, 0.4, 0.6, 0.8, 5.3],
      ]
    )
    quant_rounded_points = domain.round_one_hot_points_quantized_values(one_hot_points)
    assert numpy.all(quant_rounded_points == quant_rounded_answers)

  @flaky(max_runs=2)
  def test_snapping_points_with_temperature(self):
    num_conversions = 1000
    all_cats = [1, 2, 6, 9]
    domain = CategoricalDomain(
      [
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [1, 5]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-11.1, 4.234]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": all_cats},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [-0.1, 0, 0.1, 2]},
      ]
    )

    # This should work for all temperatures because all values are 0 except a single category
    for winning_cat_index, _ in enumerate(all_cats):
      for nonzero_value in [0.03, 0.2, 1.0]:
        cat_vals = [0] * len(all_cats)
        cat_vals[winning_cat_index] = nonzero_value
        one_hot_points = numpy.array([[3, 2.2] + cat_vals + [0.1]]) * numpy.ones((num_conversions, 1))
        for temperature in [1e-2, 1e-1, 1e0]:
          categorical_points = domain.map_one_hot_points_to_categorical(one_hot_points, temperature=temperature)
          chosen_categories = categorical_points[:, 2]
          assert all(chosen_categories == all_cats[winning_cat_index])

    # In these settings, all categories are equally desired, so we should randomly yield results
    for zero_or_nonzero_value in [0, 0.3, 1.0]:
      cat_vals = [zero_or_nonzero_value] * len(all_cats)
      one_hot_points = numpy.array([[3, 2.2] + cat_vals + [2]]) * numpy.ones((num_conversions, 1))
      uniform_proportion = 1.0 / len(all_cats)
      for temperature in [1e-2, 1e-1, 1e0]:
        categorical_points = domain.map_one_hot_points_to_categorical(one_hot_points, temperature=temperature)
        chosen_categories = categorical_points[:, 2]
        proportions = numpy.array([sum(c == chosen_categories) for c in all_cats]) / float(num_conversions)
        assert all(abs(proportions - uniform_proportion) < 0.06)

    # Check that if the first and the second categories match in value they are returned equally often
    cat_vals = [0.54321, 0.54321] + [0] * (len(all_cats) - 2)
    one_hot_points = numpy.array([[3, 2.2] + cat_vals + [0]]) * numpy.ones((num_conversions, 1))
    for temperature in [1e-2, 1e-1, 1e0]:
      categorical_points = domain.map_one_hot_points_to_categorical(one_hot_points, temperature=temperature)
      chosen_categories = categorical_points[:, 2]
      proportions = numpy.array([sum(c == chosen_categories) for c in all_cats]) / float(num_conversions)
      assert all(abs(proportions[:2] - 0.5) < 0.06)
      assert all(proportions[2:] == 0)

    # Check that if two categories are nearly equally prominent that increasing the temperature balances them out
    cat_vals = [0.63, 0.37] + [0] * (len(all_cats) - 2)
    one_hot_points = numpy.array([[3, 2.2] + cat_vals + [-0.1]]) * numpy.ones((num_conversions, 1))
    sampling_gap = []
    for temperature in [1e-2, 2e-1, 1e0, 1e1]:
      categorical_points = domain.map_one_hot_points_to_categorical(one_hot_points, temperature=temperature)
      chosen_categories = categorical_points[:, 2]
      proportions = numpy.array([sum(c == chosen_categories) for c in all_cats]) / float(num_conversions)
      sampling_gap.append(proportions[0] - proportions[1])
    assert all(numpy.diff(sampling_gap) < 0)

  def test_remove_points_outside_domain(self):
    domain = CategoricalDomain(
      [
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [10, 50]},
        {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [1, 5]},
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 3, 5]},
        {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [1.0, 2.0, 5.3]},
      ]
    )
    points = domain.generate_quasi_random_points_in_domain(10)
    points[0, :] = [23, 4, 3, 1.1]
    points[3, :] = [0, 2, 0, 1.0]
    points[6, :] = [100, 2, 3, 2.0]
    points[7, :] = [10, 2, 4, 5.3]
    points[8, :] = [50, 6, 5, 5.3]
    points_inside_domain = domain.remove_points_outside_domain(points)
    assert numpy.array_equiv(points_inside_domain, points[[1, 2, 4, 5, 9], :])

  def test_discrete_domain(self):
    domain_components = [
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [-3, 3, 7]},
      {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [0.1, 0.2, 2.4, 4.8, 23]},
    ]
    domain = CategoricalDomain(domain_components)
    discrete_elements = [
      [0, 1, 2],
      [-3, 3, 7],
      [0.1, 0.2, 2.4, 4.8, 23],
    ]

    # This domain only has 45 distinct values
    total_unique_points = 45

    num_points = numpy.random.randint(100, 150)
    points = domain.generate_quasi_random_points_in_domain(num_points)
    assert tuple(points.shape) == (num_points, domain.dim)
    assert all(domain.check_point_acceptable(p) for p in points)
    unique_random_points = domain.identify_unique_points(points)
    assert len(unique_random_points) < num_points

    all_unique_points = domain.generate_distinct_random_points(total_unique_points)
    assert len(all_unique_points) >= len(unique_random_points)
    assert len(domain.identify_unique_points(all_unique_points)) == len(all_unique_points)
    with pytest.raises(ValueError):
      # pylint: disable=protected-access
      domain._analyze_discrete_elements(discrete_elements, total_unique_points + 1, 0, 0)
      # pylint: enable=protected-access
    only_unique_points = domain.generate_distinct_random_points(total_unique_points + 1)
    assert len(all_unique_points) == len(only_unique_points) == total_unique_points

    points_already_sampled = numpy.array(
      [
        [0, 3, 2.4],
        [1, 4, 23],
        [2, 5, 7],
      ]
    )
    remaining_unique_points = domain.generate_distinct_random_points(
      total_unique_points - len(points_already_sampled),
      excluded_points=points_already_sampled,
    )
    assert len(all_unique_points) >= len(remaining_unique_points)
    assert len(domain.identify_unique_points(remaining_unique_points)) == len(remaining_unique_points)
    with pytest.raises(ValueError):
      # pylint: disable=protected-access
      domain._analyze_discrete_elements(
        discrete_elements,
        total_unique_points - len(points_already_sampled) + 1,
        len(points_already_sampled),
        0,
      )
      # pylint: enable=protected-access

    # Confirm that having points outside the domain doesn't break this computation
    points_including_outside_domain = domain.generate_quasi_random_points_in_domain(6)
    points_including_outside_domain[0, :] = [0, 0, 0]
    assert len(domain.remove_points_outside_domain(points_including_outside_domain)) == 5
    distinct_points = domain.generate_distinct_random_points(10, excluded_points=points_including_outside_domain)
    assert len(distinct_points) == 10

    # This has previously given us issues with overflow
    domain_components = [{"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10000]}] * 10
    domain = CategoricalDomain(domain_components)
    unique_random_points = domain.generate_distinct_random_points(num_points)
    assert len(unique_random_points) == num_points

    domain_components = [
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3, 4]},
    ]
    domain = CategoricalDomain(domain_components)
    assert domain.product_of_categories == 24

  @pytest.mark.parametrize("non_enum_elements", [[0.1, 0.5], ["a1", "b2"], ["1", "2"], [1.0, 2.0]])
  def test_non_enum_categoricals(self, non_enum_elements):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [3, 8]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": non_enum_elements},
    ]
    with pytest.raises(AssertionError):
      CategoricalDomain(domain_components)

  def test_all_double_domain(self):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [3, 8]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, -1]},
    ]
    domain = CategoricalDomain(domain_components)

    assert domain.product_of_categories == 1
    num_points = 86
    points = domain.generate_quasi_random_points_in_domain(num_points)
    assert points.shape == (num_points, domain.dim)
    assert numpy.all(points == domain.map_categorical_points_to_enumeration(points))
    assert numpy.all(points == domain.identify_unique_points(points))

    one_hot_points = numpy.array([domain.map_categorical_point_to_one_hot(p) for p in points])
    remapped_categorical_points = numpy.array(domain.map_one_hot_points_to_categorical(one_hot_points))
    assert numpy.all(points == remapped_categorical_points)

    one_hot_points = domain.one_hot_domain.generate_quasi_random_points_in_domain(num_points)
    categorical_points = domain.map_one_hot_points_to_categorical(one_hot_points)
    remapped_one_hot_points = numpy.array([domain.map_categorical_point_to_one_hot(p) for p in categorical_points])
    assert numpy.all(one_hot_points == remapped_one_hot_points)

  def test_constraints(self):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 5]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3, 1]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [3, 8]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [-0.2, -0.1, 1, 2.5, 10]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 3]},
    ]

    # Can't have categorical weights which are nonzero
    constraint_list = [{"weights": [1, 0, 0, 0, 2, 0, 0], "rhs": 1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME}]
    with pytest.raises(AssertionError):
      CategoricalDomain(domain_components, constraint_list)

    # Can't have constraints of the wrong size
    constraint_list = [{"weights": [1, 1, 0, 0, 0], "rhs": 1}]
    with pytest.raises(AssertionError):
      CategoricalDomain(domain_components, constraint_list)

    # Can't have missing crap
    constraint_list = [{"weights": [1, 1, 0, 0, 0, 0, 0], "rhs": 1}]
    with pytest.raises(AssertionError):
      CategoricalDomain(domain_components, constraint_list)

    constraint_list = [
      {"weights": [1, 1, 0, 0, 0, 0, 0], "rhs": 1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      {"weights": [1, 1, 1, 0, 0, 0, 0], "rhs": 2, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
    ]
    domain = CategoricalDomain(domain_components, constraint_list)

    # Actually outside domain but satisfying constraints
    assert not domain.check_point_inside([-1, 4.1, 0.4, 5, 1, -0.2, 0])
    assert domain.check_point_satisfies_constraints([-1, 4.1, 0.4, 5, 1, 2.5, 0])
    assert not domain.check_point_acceptable([-1, 4.1, 0.4, 5, 1, 10, 0])

    # In domain but not satisfying constraints
    assert domain.check_point_inside([0, 0, 0.4, 6, 2, 2.5, 0])
    assert not domain.check_point_satisfies_constraints([0, 0, 0.4, 6, 2, 2.5, 0])
    assert not domain.check_point_acceptable([0, 0, 0.4, 6, 2, 2.5, 0])

    # Not acceptable because non-integer value for integer parameter
    with pytest.raises(AssertionError):
      domain.check_point_acceptable([1, 3.3, 0.4, 3.3, 2, 2.5, 0])

    # Not acceptable because non-quantized value for quantized parameter
    assert not domain.check_point_acceptable([1, 3.3, 0.4, 3, 2, 2.2, 0])

    # Properties for integer constraints should be set properly
    integer_domain = [
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2.1, 2.1]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
      {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [-0.2, -0.1, 1, 2.5, 10]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
    ]
    constraint_list = [
      {"weights": [1, 0, 0, 1, 0, 0, 0], "rhs": 1, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
      {"weights": [0, 0, 0, 1, 0, 0, 1], "rhs": 1, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
    ]
    domain = CategoricalDomain(integer_domain, constraint_list)
    assert domain.is_integer_constrained
    assert domain.constrained_integer_indices == [0, 3, 6]

    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 5]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3, 1]},
    ]
    constraint_list = [
      {"weights": [2, 3, 0], "rhs": 1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
      {"weights": [1, 5, 2], "rhs": 2, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
    ]
    domain = CategoricalDomain(domain_components, constraint_list).one_hot_domain
    halfspace = domain.convert_func_list_to_halfspaces()
    expected_halfspace = numpy.array(
      [
        [-2, -3, 0, 1],
        [-1, -5, -2, 2],
        [-1, 0, 0, 0],
        [0, -1, 0, 0],
        [0, 0, -1, -3],
        [1, 0, 0, -2],
        [0, 1, 0, -5],
        [0, 0, 1, -1],
      ]
    )
    assert numpy.all(expected_halfspace == halfspace)

  def test_constrained_domain_construction_failures(self):
    # Constraint typing has to be consistent with domain type
    with pytest.raises(AssertionError):
      CategoricalDomain(
        domain_components=[
          {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2.1, 2.1]},
          {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2.1, 2.1]},
        ],
        constraint_list=[
          {"weights": [1.0, 1.0], "rhs": 0.3, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
        ],
      )
    with pytest.raises(AssertionError):
      CategoricalDomain(
        domain_components=[
          {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
          {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
        ],
        constraint_list=[
          {"weights": [1.0, 1.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        ],
      )

    # Can't allow mixed constraints in domain
    with pytest.raises(AssertionError):
      CategoricalDomain(
        domain_components=[
          {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
          {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2.1, 2.1]},
        ],
        constraint_list=[
          {"weights": [1.0, 1.0], "rhs": 0.3, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        ],
      )

    # Can't have non-int or non-double typing of constraint_list
    with pytest.raises(AssertionError):
      CategoricalDomain(
        domain_components=[
          {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
          {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2.1, 2.1]},
        ],
        constraint_list=[
          {"weights": [1.0, 1.0], "rhs": 0.3, "var_type": "WRONG"},
        ],
      )

  def test_prior_equality(self):
    priors = [
      {"name": ParameterPriorNames.NORMAL, "params": {"mean": 1, "scale": 2}},
      {"name": ParameterPriorNames.BETA, "params": {"shape_a": 3, "shape_b": 4}},
    ]
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2.1, 2.1]},
    ]
    domain_with_priors = CategoricalDomain(domain_components=domain_components, priors=priors)
    assert domains_approximately_equal(domain_with_priors, domain_with_priors)

    priors_unchanged = copy.deepcopy(priors)
    priors_unchanged[0] = {"name": ParameterPriorNames.NORMAL, "params": {"mean": 1.0, "scale": 2.0}}
    priors_unchanged[1] = {"name": ParameterPriorNames.BETA, "params": {"shape_a": 3.0, "shape_b": 4.0}}
    domain_with_priors_unchanged = CategoricalDomain(domain_components=domain_components, priors=priors_unchanged)
    assert domains_approximately_equal(domain_with_priors, domain_with_priors_unchanged)

    priors_changed = copy.deepcopy(priors)
    priors_changed[0] = {"name": ParameterPriorNames.BETA, "params": {"shape_a": 1, "shape_b": 2}}
    domain_with_priors_changed = CategoricalDomain(domain_components=domain_components, priors=priors_changed)
    assert not domains_approximately_equal(domain_with_priors, domain_with_priors_changed)

    priors_changed = copy.deepcopy(priors)
    priors_changed[1]["params"]["shape_a"] = 3.1
    domain_with_priors_changed = CategoricalDomain(domain_components=domain_components, priors=priors_changed)
    assert not domains_approximately_equal(domain_with_priors, domain_with_priors_changed)


class TestPriorSamplers(object):
  def test_fewer_priors_than_domain_components_raises_assertion_error(self):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 2]},
    ]
    priors = [
      {"name": ParameterPriorNames.NORMAL, "params": {"mean": 0, "scale": 1}},
    ]
    with pytest.raises(AssertionError):
      CategoricalDomain(domain_components=domain_components, priors=priors)

  @pytest.mark.parametrize(
    "var_type",
    [INT_EXPERIMENT_PARAMETER_NAME, CATEGORICAL_EXPERIMENT_PARAMETER_NAME, QUANTIZED_EXPERIMENT_PARAMETER_NAME],
  )
  def test_non_double_var_types_raise_assertion_error(self, var_type):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 2]},
    ]
    priors = [
      {"name": ParameterPriorNames.NORMAL, "params": {"mean": 0, "scale": 1}},
      None,
    ]
    domain_components[0]["var_type"] = var_type
    with pytest.raises(AssertionError):
      CategoricalDomain(domain_components=domain_components, priors=priors)

  def test_check_points_within_bounds(self):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 2]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [4, 5, 6]},
      {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [-0.2, -0.1, 1, 2.5, 10]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-4, 4]},
    ]
    priors = [
      {"name": ParameterPriorNames.NORMAL, "params": {"mean": 0, "scale": 1}},
      {"name": ParameterPriorNames.BETA, "params": {"shape_a": 3, "shape_b": 4}},
      {"name": None, "params": None},
      {"name": None, "params": None},
      {"name": None, "params": None},
      {"name": ParameterPriorNames.NORMAL, "params": {"mean": 2, "scale": 2}},
      {"name": None, "params": None},
    ]
    domain = CategoricalDomain(domain_components=domain_components, priors=priors)
    n_samples = 100
    samples = domain.generate_random_points_according_to_priors(n_samples)
    for sample in samples:
      assert domain.check_point_inside(sample)

  @flaky(max_runs=2)
  @pytest.mark.parametrize(
    "mean, scale, domain_components",
    [
      (0.05, 0.001, [0, 0.1]),
      (1, 2, [0, 3]),
      (0, 20, [10, 100]),
    ],
  )
  # The observed failure rate seems to be less than 1/10000
  def test_check_normal_prior_satisfies_distribution(self, mean, scale, domain_components):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": domain_components},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
    ]
    n_samples = 200
    priors = [
      {"name": ParameterPriorNames.NORMAL, "params": {"mean": mean, "scale": scale}},
      {"name": None, "params": None},
    ]
    domain = CategoricalDomain(domain_components=domain_components, priors=priors)
    samples = domain.generate_random_points_according_to_priors(n_samples)
    assert samples_satisfy_kolmogorov_smirnov_test(samples[:, 0], domain_components[0], priors[0])

  @flaky(max_runs=2)
  @pytest.mark.parametrize(
    "shape_a, shape_b, domain_components",
    [
      (2, 4, [0.01, 0.02]),
      (5, 5, [-1, 1]),
      (1, 3, [10, 100]),
    ],
  )
  # The observed failure rate seems to be less than 1/10000
  def test_check_unit_beta_prior_satisfies_distribution(self, shape_a, shape_b, domain_components):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": domain_components},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
    ]
    n_samples = 200
    priors = [
      {"name": ParameterPriorNames.BETA, "params": {"shape_a": shape_a, "shape_b": shape_b}},
      {"name": None, "params": None},
    ]
    domain = CategoricalDomain(domain_components=domain_components, priors=priors)
    samples = domain.generate_random_points_according_to_priors(n_samples)
    assert samples_satisfy_kolmogorov_smirnov_test(samples[:, 0], domain_components[0], priors[0])


class TestInferUnconstrainedIndicesHalfspace(object):
  domain_components = [
    {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, -1]},
    {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-1, 0]},
    {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1]},
    {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
    {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2]},
    {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-10, -2]},
    {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [2, 10]},
  ]

  @pytest.mark.parametrize(
    "constraint_list, true_nonzero_one_hot_indices",
    [
      (
        [
          {"weights": [-1, -1, 0, 0, 0, 0, 0], "rhs": -1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        ],
        [2, 3, 4, 5, 6, 7, 8],
      ),
      (
        [
          {"weights": [0, 0, 0, 0, 0, 1, 1], "rhs": -1, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
          {"weights": [-1, -1, 0, 0, 0, 0, 0], "rhs": -1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        ],
        [2, 3, 4, 5, 6],
      ),
      (
        [
          {"weights": [-1, -1, 0, 0, 0, 0, 0], "rhs": -1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
          {"weights": [0, 0, 0, 0, 0, 1, 1], "rhs": -1, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
          {"weights": [1, 1, 1, 0, 0, 0, 0], "rhs": -1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        ],
        [3, 4, 5, 6],
      ),
      (
        [
          {"weights": [-1, -1, 0, 0, 0, 0, 0], "rhs": -1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
          {"weights": [0, 0, 0, 0, 0, 1, 1], "rhs": -1, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
          {"weights": [1, 0, 0, 0, 1, 0, 0], "rhs": -1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
          {"weights": [0, 1, 1, 0, 0, 0, 0], "rhs": -1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
        ],
        [3, 4, 5],
      ),
    ],
  )
  def test_unconstrained_indices(self, constraint_list, true_nonzero_one_hot_indices):
    one_hot_domain = CategoricalDomain(self.domain_components, constraint_list=constraint_list).one_hot_domain
    one_hot_indices = one_hot_domain.one_hot_unconstrained_indices
    assert one_hot_indices == true_nonzero_one_hot_indices

  def test_unconstrained_indices_all_constraints(self):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, -1]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-1, 0]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1]},
    ]
    constraint_list = [
      {"type": "ineq", "weights": [-1, -1, -1], "rhs": 1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME}
    ]
    constraint_list = [{"weights": [-1, -1, -1], "rhs": 1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME}]
    one_hot_domain = CategoricalDomain(domain_components, constraint_list=constraint_list).one_hot_domain
    one_hot_indices = one_hot_domain.one_hot_unconstrained_indices
    assert one_hot_indices == []

  def test_unconstrained_indices_no_constraints(self):
    one_hot_domain = CategoricalDomain(self.domain_components).one_hot_domain
    one_hot_indices = one_hot_domain.one_hot_unconstrained_indices
    assert one_hot_indices == list(range(9))


class TestHitandRunSampling(object):
  def test_all_constrained(self):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [3, 5]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-3, -1]},
    ]
    constraint_list = [
      {"weights": [1, 1, 1], "rhs": 1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
    ]
    domain = CategoricalDomain(domain_components, constraint_list=constraint_list, force_hitandrun_sampling=True)
    samples = domain.generate_quasi_random_points_in_domain(10)
    assert all(domain.check_point_acceptable(point) for point in samples)

  def test_some_constrained(self):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 0]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [-0.2, -0.1, 1, 2.5, 10]},
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-20, 2]},
    ]
    constraint_list = [
      {"weights": [1, 1, 0, 0, 0, 0], "rhs": 1, "var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME},
    ]
    domain = CategoricalDomain(domain_components, constraint_list=constraint_list, force_hitandrun_sampling=True)
    samples = domain.generate_quasi_random_points_in_domain(10)
    assert all(domain.check_point_acceptable(point) for point in samples)

  def test_constrained_integers(self):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 0]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 2, 3]},
      {"var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME, "elements": [-0.2, -0.1, 1, 2.5, 10]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [0, 10]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [-20, 2]},
    ]
    constraint_list = [
      {"weights": [0, 0, 0, 0, 1, 1], "rhs": 5, "var_type": INT_EXPERIMENT_PARAMETER_NAME},
    ]
    domain = CategoricalDomain(domain_components, constraint_list=constraint_list, force_hitandrun_sampling=True)
    samples = domain.generate_quasi_random_points_in_domain(10)
    assert all(domain.check_point_acceptable(point) for point in samples)


class TestFixedIndicesOnContinuousDomain(object):
  def test_basics(self):
    cat_domain = CategoricalDomain(
      [
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 1]},
        {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [-2, 3]},
      ]
    )
    cn_domain = cat_domain.one_hot_domain

    fixed_indices = {1: 0.5}
    with pytest.raises(AssertionError):
      FixedIndicesOnContinuousDomain(cat_domain, fixed_indices)

    wrong_indices = {2: 0.5}
    with pytest.raises(AssertionError):
      FixedIndicesOnContinuousDomain(cn_domain, wrong_indices)

    wrong_fixed_value = {0: 5}
    with pytest.raises(AssertionError):
      FixedIndicesOnContinuousDomain(cn_domain, wrong_fixed_value)

    fixed_indices = {0: 0.5}
    domain = FixedIndicesOnContinuousDomain(cn_domain, fixed_indices)
    assert domain.dim == 2
    assert domain.fixed_indices == fixed_indices

  def test_point_generation(self):
    dim = numpy.random.randint(3, 6)
    cn_domain = form_random_unconstrained_categorical_domain(dim, categoricals_allowed=False).one_hot_domain
    midpoint = cn_domain.midpoint
    fixed_indices = {0: midpoint[0], 2: cn_domain.domain_bounds[2, 1]}
    domain = FixedIndicesOnContinuousDomain(cn_domain, fixed_indices)

    num_points = numpy.random.randint(10, 1000)
    random_points = domain.generate_quasi_random_points_in_domain(num_points)
    assert random_points.shape == (num_points, domain.dim)
    assert numpy.all(random_points[:, 0] == midpoint[0])
    assert numpy.all(random_points[:, 2] == cn_domain.domain_bounds[2, 1])
    assert all(cn_domain.check_point_acceptable(p) for p in random_points)

    ref_point = midpoint
    ref_point[2] = cn_domain.domain_bounds[2, 1]
    inner_points = domain.generate_random_points_near_point(num_points, ref_point, numpy.random.gamma(1, 1))
    assert all(cn_domain.check_point_acceptable(p) for p in inner_points)
    assert numpy.all(inner_points[:, 0] == midpoint[0])
    assert numpy.all(inner_points[:, 2] == cn_domain.domain_bounds[2, 1])

  def test_constraints(self):
    cn_domain = ContinuousDomain([[0, 1], [-2, 3], [-1, 2]])
    constraint_list = [
      {
        "weights": numpy.array([1, 0, 1]),
        "rhs": 1,
      }
    ]
    cn_domain.set_constraint_list(constraint_list)

    fixed_indices_is_constrained = {2: 0.25}
    with pytest.raises(AssertionError):
      FixedIndicesOnContinuousDomain(cn_domain, fixed_indices_is_constrained)

    fixed_indices = {1: 0.25}
    domain_with_constraints = FixedIndicesOnContinuousDomain(cn_domain, fixed_indices)

    num_points = 1000
    constrained_points = domain_with_constraints.generate_quasi_random_points_in_domain(num_points)
    assert all(constrained_points[:, 0] + constrained_points[:, 2] > 1)
    assert all(constrained_points[:, 1] == 0.25)
    assert all(cn_domain.check_point_satisfies_constraints(p) for p in constrained_points)
    assert all(cn_domain.check_point_acceptable(p) for p in constrained_points)

  def test_restrict_points_to_constrained_domain(self):
    cn_domain = ContinuousDomain([[0, 1], [-2, 3], [-1, 2]])
    constraint_list = [
      {
        "weights": numpy.array([1, 0, 1]),
        "rhs": 1,
      }
    ]
    cn_domain.set_constraint_list(constraint_list)

    fixed_indices = {1: 0.25}
    domain_with_constraints = FixedIndicesOnContinuousDomain(cn_domain, fixed_indices)
    domain = FixedIndicesOnContinuousDomain(
      ContinuousDomain([[0, 1], [-2, 3], [-1, 2]]),
      fixed_indices,
    )
    num_points = 1000

    unconstrained_points = domain.generate_quasi_random_points_in_domain(num_points)
    unconstrained_points[-1, :] = [0, 0, 0]  # Does not satisfy the constraints
    constrained_points = domain_with_constraints.restrict_points_to_domain(unconstrained_points)
    assert not numpy.allclose(unconstrained_points, constrained_points)
    assert any(unconstrained_points[:, 0] + unconstrained_points[:, 2] <= 1)
    assert all(constrained_points[:, 0] + constrained_points[:, 2] > 1)
    assert all(cn_domain.check_point_satisfies_constraints(p) for p in constrained_points)
    assert all(cn_domain.check_point_satisfies_constraints(p) == (p[0] + p[2] > 1) for p in unconstrained_points)

    constrained_points_on = domain_with_constraints.restrict_points_to_domain(
      unconstrained_points,
      on_constraint=True,
    )
    assert not numpy.allclose(unconstrained_points, constrained_points_on)
    on_constraint = constrained_points_on[:, 0] + constrained_points_on[:, 2] < 1
    assert numpy.allclose(
      constrained_points_on[on_constraint, 0] + constrained_points_on[on_constraint, 2],
      1,
    )
