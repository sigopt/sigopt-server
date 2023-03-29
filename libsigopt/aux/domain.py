# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from collections import OrderedDict

import numpy
from scipy.spatial.distance import cdist
from scipy.stats import beta, truncnorm

from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  QUANTIZED_EXPERIMENT_PARAMETER_NAME,
  ParameterPriorNames,
)
from libsigopt.aux.geometry_utils import find_interior_point
from libsigopt.aux.samplers import (
  generate_grid_points,
  generate_halton_points,
  generate_hitandrun_random_points,
  generate_latin_hypercube_points,
  generate_sobol_points,
  generate_uniform_random_points,
  generate_uniform_random_points_rejection_sampling_with_hitandrun_padding,
)


DEFAULT_QUASI_RANDOM_SAMPLER = "latin_hypercube"
DEFAULT_SAFETY_MARGIN_FOR_CONSTRAINTS = 1e-8
MAX_DISCRETE_DOMAIN_UNIQUENESS_SEARCH = 100000
DEFAULT_ONE_HOT_SNAPPING_TEMPERATURE = 0.2
MINIMUM_ONE_HOT_SNAPPING_TEMPERATURE = 0.01
DEFAULT_NUM_RANDOM_NEIGHBORS = 10000
MAX_GRID_DIM = 13


def form_constraint_fun_and_jac(one_hot_weights, rhs):
  def fun(one_hot_x):
    return numpy.dot(one_hot_weights, one_hot_x.T) - (1 + DEFAULT_SAFETY_MARGIN_FOR_CONSTRAINTS * numpy.sign(rhs)) * rhs

  def jac(one_hot_x):
    return one_hot_weights

  return fun, jac


def is_valid_prior(prior):
  return bool(prior and prior["name"] is not None and prior["params"] is not None)


def find_indexes_of_unique_points(points, compare_points, scaling_vector, tolerance):
  assert len(points.shape) == 2
  n_dim = points.shape[1]
  if compare_points is None:
    # NOTE: tril excludes indexes later in points, preferring points found earlier in CL
    distance_matrix = cdist(points, points, "seuclidean", V=numpy.array(scaling_vector, dtype=float))
    distance_matrix += numpy.tril(numpy.full_like(distance_matrix, tolerance + 1))
  else:
    distance_matrix = cdist(compare_points, points, "seuclidean", V=numpy.array(scaling_vector, dtype=float))
  unique_indexes = numpy.all(distance_matrix > tolerance * numpy.sqrt(n_dim), axis=0)
  return unique_indexes


class ContinuousDomain(object):
  def __init__(self, domain_bounds):
    """Construct a ContinuousDomain with the specified bounds."""
    bounds_shape = numpy.asarray(domain_bounds).shape
    assert len(bounds_shape) == 2
    assert bounds_shape[1] == 2
    assert numpy.all(numpy.diff(domain_bounds, axis=1) >= 0)
    self.domain_bounds = numpy.copy(domain_bounds)
    self._quasi_random_sampler_opts = {"sampler": DEFAULT_QUASI_RANDOM_SAMPLER}
    self._constraint_list = []
    self._one_hot_unconstrained_indices = list(range(self.dim))
    self._halfspaces = None
    self._cheby_center = None
    self.force_hitandrun_sampling = False

  def __repr__(self):
    if not self.is_constrained:
      return f"ContinuousDomain({self.domain_bounds})"
    return f"ContinuousDomain({self.domain_bounds})\nConstraints({self._halfspaces})"

  @property
  def dim(self):
    """Return the number of spatial dimensions."""
    return len(self.domain_bounds)

  @property
  def midpoint(self):
    return numpy.mean(self.get_lower_upper_bounds(), axis=0)

  @property
  def one_hot_halfspaces(self):
    return self._halfspaces

  @property
  def is_constrained(self):
    return bool(self._constraint_list)

  @property
  def one_hot_unconstrained_indices(self):
    return self._one_hot_unconstrained_indices

  def set_quasi_random_sampler_opts(self, **kwargs):
    """Input a dictionary of options for the quasi random sampler."""
    possible_quasi_random_samplers = ("latin_hypercube", "halton", "sobol", "uniform")
    if "sampler" not in kwargs:
      raise AttributeError("Options must include sampler to define quasi-random points")
    elif kwargs["sampler"] not in possible_quasi_random_samplers:
      raise ValueError(f'The sampler {kwargs["sampler"]} does not exist')
    else:
      self._quasi_random_sampler_opts = kwargs

  def get_quasi_random_sampler_opts(self):
    """Recover the dictionary of options for the quasi random sampler."""
    return copy.deepcopy(self._quasi_random_sampler_opts)

  quasi_random_sampler_opts = property(get_quasi_random_sampler_opts, set_quasi_random_sampler_opts)

  def check_point_inside(self, point):
    return numpy.all((point >= self.domain_bounds[:, 0]) & (point <= self.domain_bounds[:, 1]))

  def check_point_on_boundary(self, point, tol=0):
    if not self.is_constrained:
      return numpy.any(numpy.abs(point - self.domain_bounds.T) <= tol)

    return any(numpy.abs(numpy.dot(self._halfspaces[:, :-1], point) + self._halfspaces[:, -1]) <= tol)

  def check_point_satisfies_constraints(self, point):
    if not self.is_constrained:
      return True
    A = self._halfspaces[:, :-1]
    b = -self._halfspaces[:, -1]
    return all(list(numpy.dot(A, point) <= b))

  def check_point_acceptable(self, point):
    assert len(point) == self.dim
    return self.check_point_inside(point) and self.check_point_satisfies_constraints(point)

  def set_constraint_list(self, constraint_list):
    """Set a the list of constraints (excluding bounds)."""
    if constraint_list:
      self._constraint_list = constraint_list
      self._halfspaces = self.convert_func_list_to_halfspaces()
      self._one_hot_unconstrained_indices = self._infer_unconstrained_indices_from_halfspace()
      self._cheby_center, __, feasibility = find_interior_point(self._halfspaces)
      assert feasibility
    else:
      self._constraint_list = []
      self._halfspaces = None
      self._one_hot_unconstrained_indices = list(range(self.dim))
      self._cheby_center = None

  def get_constraints_for_scipy(self):
    if not self.is_constrained:
      return []

    scipy_constraints = []
    for con in self._constraint_list:
      fun, jac = form_constraint_fun_and_jac(con["weights"], con["rhs"])
      scipy_constraints.append(
        {
          "type": "ineq",
          "fun": fun,
          "jac": jac,
        }
      )
    return scipy_constraints

  def convert_func_list_to_halfspaces(self):
    n_halfspaces = len(self._constraint_list)
    halfspaces = numpy.zeros((n_halfspaces, self.dim + 1))

    for ic, constraint in enumerate(self._constraint_list):
      halfspaces[ic, -1] = constraint["rhs"]
      halfspaces[ic, :-1] = -constraint["weights"]

    lower_bound_halfspaces = -numpy.eye(self.dim, M=self.dim + 1)
    lower_bound_halfspaces[:, -1] = self.domain_bounds[:, 0]
    upper_bound_halfspaces = numpy.eye(self.dim, M=self.dim + 1)
    upper_bound_halfspaces[:, -1] = -self.domain_bounds[:, 1]

    return numpy.vstack((halfspaces, lower_bound_halfspaces, upper_bound_halfspaces))

  def _infer_unconstrained_indices_from_halfspace(self):
    return [i for i in range(self.dim) if numpy.count_nonzero(self.one_hot_halfspaces[:, i]) == 2]

  def get_lower_upper_bounds(self):
    return self.domain_bounds.T

  def generate_quasi_random_points_in_domain(self, num_points, log_sample=False):
    """Generate quasi-random points in the domain."""
    if log_sample:
      domain_bounds = numpy.log(self.domain_bounds)
    else:
      domain_bounds = self.domain_bounds

    if self._quasi_random_sampler_opts.get("sampler") is None:
      raise AttributeError("You must call set_quasi_random_sampler_opts before generating quasi-random points.")
    elif self.is_constrained:
      x0 = self._cheby_center
      A = self._halfspaces[:, :-1]
      b = -self._halfspaces[:, -1]
      if self.force_hitandrun_sampling:
        points = generate_hitandrun_random_points(num_points, x0, A, b)

        # Note: if there are unconstrained parameters present, their distribution tends to have a bit of bias
        # towards the middle of the domain. We deal with this by replacing these samples with uniform random. This is
        # a bit inefficient but does solve the problem.
        points[:, self.one_hot_unconstrained_indices] = generate_uniform_random_points(
          num_points,
          domain_bounds[self.one_hot_unconstrained_indices, :],
        )
      else:
        points, success = generate_uniform_random_points_rejection_sampling_with_hitandrun_padding(
          num_points,
          domain_bounds,
          A,
          b,
          x0,
        )
        self.force_hitandrun_sampling = not success
    elif self._quasi_random_sampler_opts["sampler"] == "latin_hypercube":
      points = generate_latin_hypercube_points(num_points, domain_bounds)
    elif self._quasi_random_sampler_opts["sampler"] == "halton":
      points = generate_halton_points(
        num_points,
        domain_bounds,
        skip=self._quasi_random_sampler_opts.get("skip"),
        seed=self._quasi_random_sampler_opts.get("seed"),
      )
    elif self._quasi_random_sampler_opts["sampler"] == "uniform":
      points = generate_uniform_random_points(num_points, domain_bounds)
    elif self._quasi_random_sampler_opts["sampler"] == "sobol":
      points = generate_sobol_points(
        num_points,
        domain_bounds,
        skip=self._quasi_random_sampler_opts.get("skip"),
        seed=self._quasi_random_sampler_opts.get("seed"),
      )
    else:
      raise ValueError("Somehow the quasi random points you are asking for do not exist")
    return numpy.exp(points) if log_sample else points

  def generate_grid_points_in_domain(self, points_per_dimension):
    return generate_grid_points(points_per_dimension, self.domain_bounds)

  def restrict_points_using_constraints(self, points, viable_point=None, on_constraint=False):
    if not self.is_constrained:
      return

    if viable_point is None or not self.check_point_acceptable(viable_point):
      viable_point = self._cheby_center
    elif self.check_point_on_boundary(viable_point, DEFAULT_SAFETY_MARGIN_FOR_CONSTRAINTS):
      # viable point needs to be inside. Push it towards the center
      viable_point = viable_point + (self._cheby_center - viable_point) * 0.01

    A, b = self._halfspaces[:, :-1], -self._halfspaces[:, -1]

    # remove the constraints that are the domain_bounds
    no_bound_idxs = numpy.where(numpy.sum(A != 0, axis=1) > 1)[0]
    A, b = A[no_bound_idxs], b[no_bound_idxs]

    A_normal = numpy.dot(A, points.T)
    slack = b[:, None] - A_normal
    viable_point_minus_A_normal = numpy.dot(A, viable_point)[:, None] - A_normal
    multipliers = numpy.divide(
      slack, viable_point_minus_A_normal, out=numpy.zeros_like(slack), where=viable_point_minus_A_normal != 0
    )

    valid_multipliers = numpy.logical_and(multipliers > 0, multipliers < 1)
    indices_need_corrected = numpy.any(valid_multipliers, axis=0)

    if not any(indices_need_corrected):
      return

    multipliers[~valid_multipliers] = 0
    max_correction = numpy.max(multipliers[:, indices_need_corrected], axis=0)

    epsilon_shift = 1.0 - max_correction
    if not on_constraint:
      epsilon_shift *= numpy.random.random(len(epsilon_shift))

    points[indices_need_corrected] *= epsilon_shift[:, None]
    points[indices_need_corrected] += (1.0 - epsilon_shift[:, None]) * viable_point[None, :]

  def restrict_points_to_domain(self, points, on_constraint=False, viable_point=None):
    lb, ub = self.get_lower_upper_bounds()
    restricted_points = numpy.clip(points, lb, ub)
    self.restrict_points_using_constraints(
      restricted_points,
      viable_point=viable_point,
      on_constraint=on_constraint,
    )
    return restricted_points

  def generate_random_points_near_point(self, num_points, point, std_dev, on_constraint=False):
    assert point.shape == (self.dim,)
    if not self.check_point_acceptable(point):
      return self.generate_quasi_random_points_in_domain(num_points)

    normal_draws = numpy.random.normal(0, std_dev, (num_points, self.dim))
    normal_draws = self.restrict_points_to_domain(
      point[None, :] + normal_draws * numpy.diff(self.get_lower_upper_bounds(), axis=0),
      viable_point=point,
      on_constraint=on_constraint,
    )
    return normal_draws


class CategoricalDomain(object):
  def __init__(self, domain_components, constraint_list=None, force_hitandrun_sampling=False, priors=None):
    """Construct a mixed continuous/categorical domain with the specified info.

        ** Sample domain_components dict **
        domain_components = [
          dict(var_type="double", elements=[-2, 5]),
          dict(var_type="int", elements=[1, 10]),
          dict(var_type="categorical", elements=[0, 1, 2]),
          dict(var_type="quantized", elements[0.2, 1.3, 2.5]),
        ]

        NOTE: For now we only allow uniform random sampling (maybe at some point quasi random as well)
        TODO(RTL-97): Tighten up this initialization component a little
        """
    assert constraint_list or not force_hitandrun_sampling
    self._verify_domain_components(domain_components, constraint_list, priors)
    self.domain_components = copy.deepcopy(domain_components)
    self.constraint_list = copy.deepcopy(constraint_list or [])
    self.priors = copy.deepcopy(priors or [])

    self.one_hot_domain, self.one_hot_to_categorical_mapping = self.form_one_hot_domain(self.domain_components)
    self.one_hot_domain.force_hitandrun_sampling = force_hitandrun_sampling
    self.one_hot_constraint_list = self._form_one_hot_constraint_list()
    self.one_hot_domain.set_constraint_list(self.one_hot_constraint_list)
    self.constrained_double_indices, self.constrained_integer_indices = self._form_constrained_variable_indices()
    self.integer_constraint_function_indices = self._form_integer_constraint_function_indices()

  def __repr__(self):
    return "domain_components:" + repr(self.domain_components) + "\n" + "constraint_list:" + repr(self.constraint_list)

  def __iter__(self):
    return iter(self.domain_components)

  @staticmethod
  def _verify_domain_components(domain_components, constraint_list, priors):
    for component in domain_components:
      assert "var_type" in component and "elements" in component
      assert component["var_type"] in (
        CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
        INT_EXPERIMENT_PARAMETER_NAME,
        DOUBLE_EXPERIMENT_PARAMETER_NAME,
        QUANTIZED_EXPERIMENT_PARAMETER_NAME,
      )
      if component["var_type"] in (CATEGORICAL_EXPERIMENT_PARAMETER_NAME, QUANTIZED_EXPERIMENT_PARAMETER_NAME):
        assert len(component["elements"]) > 1
        assert len(set(component["elements"])) == len(component["elements"])
        if component["var_type"] == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
          assert all(isinstance(v, int) for v in component["elements"]), "Only allow enum index like elements."
        if component["var_type"] == QUANTIZED_EXPERIMENT_PARAMETER_NAME:
          assert numpy.all(numpy.isfinite(component["elements"]))
      else:
        assert len(component["elements"]) == 2
        assert component["elements"][0] < component["elements"][1]
        if component["var_type"] == INT_EXPERIMENT_PARAMETER_NAME:
          assert all(int(v) == v for v in component["elements"])

    if constraint_list:
      for constraint in constraint_list:
        assert "weights" in constraint and "rhs" in constraint and "var_type" in constraint
        assert constraint["var_type"] in [DOUBLE_EXPERIMENT_PARAMETER_NAME, INT_EXPERIMENT_PARAMETER_NAME]
        assert len(constraint["weights"]) == len(domain_components)

        # Check that typing between constraint and domain_components is consistent
        non_zero_indices = numpy.flatnonzero(constraint["weights"])
        for idx in non_zero_indices:
          assert domain_components[idx]["var_type"] == constraint["var_type"]

        # Check that weights are zero for non-integer and non-double variables
        for weight, component in zip(constraint["weights"], domain_components):
          if component["var_type"] not in [DOUBLE_EXPERIMENT_PARAMETER_NAME, INT_EXPERIMENT_PARAMETER_NAME]:
            assert weight == 0

    if priors:
      assert len(priors) == len(domain_components)
      for prior, component in zip(priors, domain_components):
        if prior["name"] is not None:
          assert component["var_type"] == DOUBLE_EXPERIMENT_PARAMETER_NAME

  @property
  def dim(self):
    return len(self.domain_components)

  @property
  def is_continuous(self):
    return all(c["var_type"] == DOUBLE_EXPERIMENT_PARAMETER_NAME for c in self)

  @property
  def is_discrete(self):
    return all(c["var_type"] != DOUBLE_EXPERIMENT_PARAMETER_NAME for c in self)

  @property
  def is_constrained(self):
    return bool(self.constraint_list)

  @property
  def is_integer_constrained(self):
    if not self.is_constrained:
      return False

    for constraint in self.constraint_list:
      if constraint["var_type"] == INT_EXPERIMENT_PARAMETER_NAME:
        return True
    return False

  @property
  def one_hot_dim(self):
    return self.one_hot_domain.dim

  @property
  def force_hitandrun_sampling(self):
    return self.one_hot_domain.force_hitandrun_sampling

  @property
  def has_categoricals(self):
    return any(c["var_type"] == CATEGORICAL_EXPERIMENT_PARAMETER_NAME for c in self)

  @property
  def has_quantized(self):
    return any(c["var_type"] == QUANTIZED_EXPERIMENT_PARAMETER_NAME for c in self)

  # TODO(RTL-151): Maybe consider combining all three methods below if we have iterate through many constraints
  def _form_integer_constraint_function_indices(self):
    return [
      i for i, constraint in enumerate(self.constraint_list) if constraint["var_type"] == INT_EXPERIMENT_PARAMETER_NAME
    ]

  def _form_constrained_variable_indices(self):
    constrained_integer_indices = []
    constrained_double_indices = []
    if self.constraint_list:
      for constraint in self.constraint_list:
        if constraint["var_type"] == DOUBLE_EXPERIMENT_PARAMETER_NAME:
          constraint_indices = numpy.flatnonzero(constraint["weights"])
          constrained_double_indices.extend(constraint_indices)
        elif constraint["var_type"] == INT_EXPERIMENT_PARAMETER_NAME:
          constraint_indices = numpy.flatnonzero(constraint["weights"])
          constrained_integer_indices.extend(constraint_indices)
    return list(set(constrained_double_indices)), list(set(constrained_integer_indices))

  def _form_one_hot_constraint_list(self):
    one_hot_constraint_list = []
    for constraint in self.constraint_list:
      one_hot_weights = numpy.zeros(self.one_hot_dim)
      for weight, reference in zip(constraint["weights"], self.one_hot_to_categorical_mapping):
        if reference["var_type"] in [DOUBLE_EXPERIMENT_PARAMETER_NAME, INT_EXPERIMENT_PARAMETER_NAME]:
          one_hot_weights[reference["input_ind"]] = weight

      one_hot_constraint_list.append(
        {
          "rhs": constraint["rhs"],
          "var_type": constraint["var_type"],
          "weights": one_hot_weights,
        }
      )
    return one_hot_constraint_list

  def get_integer_one_hot_constraint_matrices(self):
    A = self.one_hot_domain.one_hot_halfspaces[self.integer_constraint_function_indices, :-1]
    b = -self.one_hot_domain.one_hot_halfspaces[self.integer_constraint_function_indices, -1]
    return A, b

  def generate_integer_neighbors_for_integer_constraints(self, one_hot_point):
    """Generates neighboring integers of one_hot_point"""
    assert self.is_integer_constrained

    # check to make sure one_hot_point has integers where the constrained indices are
    one_hot_constrained_integer_indices = [
      self.one_hot_to_categorical_mapping[i]["input_ind"] for i in self.constrained_integer_indices
    ]
    n_constrained_integers = len(one_hot_constrained_integer_indices)
    ub = numpy.ceil(one_hot_point[one_hot_constrained_integer_indices])
    lb = numpy.floor(one_hot_point[one_hot_constrained_integer_indices])

    # Generate neighbor points
    if n_constrained_integers <= MAX_GRID_DIM:  # Grid if dim <= MAX_GRID_DIM
      num_neighbors = 2**n_constrained_integers
      grids = numpy.meshgrid(*list(zip(lb, ub)))
      neighbors_int_variables = numpy.array([grid.flatten() for grid in grids]).T
    else:  # Random otherwise
      num_neighbors = DEFAULT_NUM_RANDOM_NEIGHBORS
      subdomain_bounds = numpy.array(list(zip(lb, ub)))
      neighbors_int_variables = numpy.round(generate_uniform_random_points(num_neighbors, subdomain_bounds))
    integer_neighbors = numpy.tile(one_hot_point, (num_neighbors, 1))
    integer_neighbors[:, one_hot_constrained_integer_indices] = neighbors_int_variables

    return integer_neighbors

  def map_categorical_points_to_enumeration(self, points):
    if not self.has_categoricals:
      return points

    # Copy data so as to not overwrite original info
    points = numpy.atleast_2d(numpy.array(points, dtype=float))
    for dim_index, (points_1d, component) in enumerate(zip(points.T, self.domain_components)):
      if component["var_type"] == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
        map_to_enumeration = dict(zip(component["elements"], range(len(component["elements"]))))
        points[:, dim_index] = [map_to_enumeration[p] for p in points_1d]
    return points

  @staticmethod
  def _check_1d_point_inside(point_1d, domain_component):
    if domain_component["var_type"] in (
      CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
      QUANTIZED_EXPERIMENT_PARAMETER_NAME,
    ):
      return point_1d in domain_component["elements"]
    else:
      if domain_component["var_type"] == INT_EXPERIMENT_PARAMETER_NAME:
        assert int(point_1d) == point_1d
      return domain_component["elements"][0] <= point_1d <= domain_component["elements"][1]

  @staticmethod
  def _check_enumerated_point_satisfies_constraint(enumerated_point, constraint):
    return numpy.dot(enumerated_point, constraint["weights"]) >= constraint["rhs"]

  # NOTE: This assumes that test_points is a numpy array
  # This function cuts points which are less than some normalized tolerance from each other
  def identify_unique_points(self, test_points, compare_points=None, tolerance=0.0):
    points = self.map_categorical_points_to_enumeration(test_points)
    compare_points = None if compare_points is None else self.map_categorical_points_to_enumeration(compare_points)

    scaling_vector = []
    for dc in self.domain_components:
      if dc["var_type"] == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
        scaling_vector.append(len(dc["elements"]))
      elif dc["var_type"] == QUANTIZED_EXPERIMENT_PARAMETER_NAME:
        scaling_vector.append(max(dc["elements"]) - min(dc["elements"]))
      else:
        scaling_vector.append(dc["elements"][1] - dc["elements"][0])

    unique_indexes = find_indexes_of_unique_points(points, compare_points, scaling_vector, tolerance)
    return test_points[unique_indexes, :]

  def check_point_satisfies_constraints(self, point):
    if not self.is_constrained:
      return True
    enumerated_point = self.map_categorical_points_to_enumeration([point])[0]
    return all(self._check_enumerated_point_satisfies_constraint(enumerated_point, c) for c in self.constraint_list)

  def check_point_inside(self, point):
    return all(self._check_1d_point_inside(p, c) for p, c in zip(point, self.domain_components))

  def check_point_acceptable(self, point):
    assert len(point) == self.dim
    return self.check_point_inside(point) and self.check_point_satisfies_constraints(point)

  def get_integer_component_mappings(self):
    return [m for m in self.one_hot_to_categorical_mapping if m["var_type"] == INT_EXPERIMENT_PARAMETER_NAME]

  def get_categorical_component_mappings(self):
    return [m for m in self.one_hot_to_categorical_mapping if m["var_type"] == CATEGORICAL_EXPERIMENT_PARAMETER_NAME]

  def get_quantized_component_mappings(self):
    return [m for m in self.one_hot_to_categorical_mapping if m["var_type"] == QUANTIZED_EXPERIMENT_PARAMETER_NAME]

  @property
  def product_of_categories(self):
    cat_shape = [len(m["input_ind_value_map"]) for m in self.get_categorical_component_mappings()]
    return numpy.prod(cat_shape, dtype=int)

  def _generate_quasi_random_1d_points_in_domain(self, num_points, domain_component):
    if domain_component["var_type"] in (CATEGORICAL_EXPERIMENT_PARAMETER_NAME, QUANTIZED_EXPERIMENT_PARAMETER_NAME):
      return numpy.random.choice(domain_component["elements"], replace=True, size=num_points)
    elif domain_component["var_type"] == INT_EXPERIMENT_PARAMETER_NAME:
      return numpy.random.randint(domain_component["elements"][0], domain_component["elements"][1] + 1, num_points)
    else:
      return numpy.random.uniform(domain_component["elements"][0], domain_component["elements"][1], num_points)

  def _generate_random_1d_points_according_to_prior(self, num_points, component, prior):
    if not is_valid_prior(prior):
      return self._generate_quasi_random_1d_points_in_domain(num_points, component)

    param_bound_minimum = component["elements"][0]
    param_bound_maximum = component["elements"][1]
    if prior["name"] == ParameterPriorNames.NORMAL:
      random_values = truncnorm.rvs(
        (param_bound_minimum - prior["params"]["mean"]) / prior["params"]["scale"],
        (param_bound_maximum - prior["params"]["mean"]) / prior["params"]["scale"],
        prior["params"]["mean"],
        prior["params"]["scale"],
        size=num_points,
      )
    elif prior["name"] == ParameterPriorNames.BETA:
      random_values = beta.rvs(
        prior["params"]["shape_a"],
        prior["params"]["shape_b"],
        param_bound_minimum,
        param_bound_maximum - param_bound_minimum,
        size=num_points,
      )
    else:
      raise ValueError(f"Unknown prior name: {prior['name']}")
    return random_values

  def generate_random_points_according_to_priors(self, num_points):
    assert self.priors, "There are no priors; must have priors to call this function"
    result = numpy.empty((num_points, self.dim))
    for d, (prior, component) in enumerate(zip(self.priors, self.domain_components)):
      result[:, d] = self._generate_random_1d_points_according_to_prior(num_points, component, prior)
    return result

  def generate_quasi_random_points_in_domain(self, num_points):
    if self.constraint_list:
      # Note: due to integer constraints, we may return less than num_points samples.
      one_hot_constrained_points = self.one_hot_domain.generate_quasi_random_points_in_domain(num_points)
      result = self.map_one_hot_points_to_categorical(one_hot_constrained_points)
    else:
      result = numpy.empty((num_points, self.dim))
      for d, component in enumerate(self.domain_components):
        result[:, d] = self._generate_quasi_random_1d_points_in_domain(num_points, component)
    return result

  # This function is a supporter for generate_distinct_random_points to deal with potential overflow issues
  @staticmethod
  def _analyze_discrete_elements(
    discrete_elements,
    num_points_to_sample,
    num_points_already_sampled,
    duplicate_prob,
  ):
    num_total_discrete_values = 1.0
    for de in discrete_elements:
      num_total_discrete_values *= len(de)
      if num_total_discrete_values >= MAX_DISCRETE_DOMAIN_UNIQUENESS_SEARCH:
        return None, True  # Should generate points randomly

    num_total_discrete_values = int(num_total_discrete_values)

    if num_points_to_sample > num_total_discrete_values:
      raise ValueError(f"{num_points_to_sample} is more points than exist uniquely in this domain")
    if num_points_to_sample + num_points_already_sampled > num_total_discrete_values:
      raise ValueError(
        (
          f"{num_points_to_sample} unique points do not exist in this domain,"
          f" given that {num_points_already_sampled} have been sampled"
        ),
      )

    if num_points_to_sample + num_points_already_sampled <= duplicate_prob * num_total_discrete_values:
      return num_total_discrete_values, True

    return num_total_discrete_values, False

  # NOTE: If a large number of points will be out of the domain, could be made more efficient
  #       by only testing points which were previously acceptable
  def remove_points_outside_domain(self, points):
    (num_points, dim) = points.shape
    assert dim == self.dim, f"Incorrect dimension for points {dim}"
    if not num_points:
      return points

    still_in = numpy.full(len(points), True, dtype=bool)
    for this_dim_points, this_component in zip(points.T, self):
      if this_component["var_type"] == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
        still_in[still_in] = numpy.isin(this_dim_points[still_in], this_component["elements"])
      elif this_component["var_type"] == QUANTIZED_EXPERIMENT_PARAMETER_NAME:
        still_in[still_in] = numpy.isin(this_dim_points[still_in].astype(float), this_component["elements"])
      else:
        still_in[still_in] = numpy.logical_and(
          this_dim_points[still_in].astype(float) >= this_component["elements"][0],
          this_dim_points[still_in].astype(float) <= this_component["elements"][1],
        )
    return points[still_in, :]

  # This is for use when the domain is discrete and we want to avoid sampling points we have already considered
  # duplicate_prob is the allowed prob of a duplicate for too large of a discrete domain
  # TODO(RTL-100): We should consider enlarging the functionality here to deal with duplicate points
  def generate_distinct_random_points(self, num_points, excluded_points=None, duplicate_prob=1e-3):
    if num_points == 0:
      return numpy.empty((0, self.dim))
    if not self.is_discrete or self.is_constrained:
      return self.generate_quasi_random_points_in_domain(num_points)
    excluded_points = numpy.empty((0, self.dim)) if excluded_points is None else excluded_points
    excluded_points = self.remove_points_outside_domain(excluded_points)

    discrete_elements = []
    for dc in self.domain_components:
      if dc["var_type"] in (CATEGORICAL_EXPERIMENT_PARAMETER_NAME, QUANTIZED_EXPERIMENT_PARAMETER_NAME):
        discrete_elements.append(dc["elements"])
      else:
        discrete_elements.append(list(range(int(dc["elements"][0]), int(dc["elements"][1] + 1))))

    try:
      num_total_discrete_values, should_generate_randomly = self._analyze_discrete_elements(
        discrete_elements,
        num_points,
        len(excluded_points),
        duplicate_prob,
      )
    except ValueError:
      should_generate_randomly = False
      num_total_discrete_values, _ = self._analyze_discrete_elements(discrete_elements, 0, 0, 0)
      num_points = num_total_discrete_values - len(excluded_points)
      if num_points <= 0:
        return numpy.empty((0, self.dim))

    if should_generate_randomly or num_total_discrete_values is None:
      return self.generate_quasi_random_points_in_domain(num_points)

    def map_index_to_discrete_point(index):
      pt = []
      for k, b in enumerate([len(d) for d in discrete_elements]):
        pt.append(discrete_elements[k][int(index % b)])
        index = (index - index % b) / b
      return pt

    def map_discrete_point_to_index(point):
      index = 0
      base_factor = 1
      for p, element in zip(point, discrete_elements):
        index += numpy.nonzero([p == e for e in element])[0][0] * base_factor
        base_factor *= len(element)
      return index

    excluded_indexes = {map_discrete_point_to_index(p) for p in excluded_points}
    available_indexes = set(range(num_total_discrete_values)) - excluded_indexes
    if len(available_indexes) > num_points:
      unique_indexes = numpy.random.choice(tuple(available_indexes), num_points, replace=False)
    else:
      unique_indexes = numpy.append(
        numpy.array(tuple(available_indexes)),
        numpy.random.randint(0, num_total_discrete_values + 1, num_points - len(available_indexes)),
      )

    return numpy.array([map_index_to_discrete_point(i) for i in unique_indexes])

  def replace_duplicate_points(self, points, points_sampled, tolerance=0.0):
    # NOTE: identify_unique_points checks duplicates between points and compare_points
    # when the latter is not None, and checks duplicates within itself when it is None.
    unique_points = self.identify_unique_points(points, tolerance=tolerance)
    unique_points = self.identify_unique_points(
      unique_points,
      compare_points=points_sampled,
      tolerance=tolerance,
    )

    return numpy.append(
      unique_points,
      self.generate_distinct_random_points(len(points) - len(unique_points), points_sampled),
      axis=0,
    )

  @staticmethod
  def form_one_hot_domain(domain_components):
    domain_bounds = []
    one_hot_to_categorical_mapping = []
    oh_num = 0
    for component_num, component in enumerate(domain_components):
      this_mapping = {"var_type": component["var_type"], "output_ind": component_num}
      if component["var_type"] in (DOUBLE_EXPERIMENT_PARAMETER_NAME, INT_EXPERIMENT_PARAMETER_NAME):
        this_mapping.update({"input_ind": oh_num})
        domain_bounds.append(component["elements"])
        oh_num += 1
      elif component["var_type"] == QUANTIZED_EXPERIMENT_PARAMETER_NAME:
        this_mapping.update({"input_ind": oh_num})
        domain_bounds.append([min(component["elements"]), max(component["elements"])])
        oh_num += 1
      else:
        elements = component["elements"]
        this_mapping.update({"input_ind_value_map": OrderedDict(zip(range(oh_num, oh_num + len(elements)), elements))})
        domain_bounds.extend([[0, 1]] * len(elements))
        oh_num += len(elements)
      one_hot_to_categorical_mapping.append(this_mapping)

    return ContinuousDomain(domain_bounds), one_hot_to_categorical_mapping

  # TODO(RTL-101): Provide mechanism for doing this in vectorized form
  def map_categorical_point_to_one_hot(self, categorical_point):
    if not self.has_categoricals:
      return categorical_point

    one_hot_point = []
    for this_cat_ind_value, component in zip(categorical_point, self.domain_components):
      if component["var_type"] == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
        assert this_cat_ind_value in component["elements"], f'{this_cat_ind_value}, {component["elements"]}'
        for element in component["elements"]:
          one_hot_point.append(1 if this_cat_ind_value == element else 0)
      else:
        one_hot_point.append(this_cat_ind_value)
    return one_hot_point

  # NOTE: This imposes a specific belief about the hyperparameters that could change at some point.
  def map_categorical_length_scales_to_one_hot(self, categorical_length_scales):
    LION_LENGTH_SCALE = 1.0  # HACK: Trying this for now -- can pass intelligently later
    one_hot_length_scales = []
    for categorical_length_scale, component in zip(categorical_length_scales, self.domain_components):
      if None in categorical_length_scale:  # Only true for default value categorical variables
        one_hot_length_scales.extend([LION_LENGTH_SCALE] * len(component["elements"]))
      else:
        one_hot_length_scales.extend(categorical_length_scale)
    return one_hot_length_scales

  def map_one_hot_length_scales_to_categorical(self, one_hot_length_scales):
    categorical_length_scales = []
    for mapping, component in zip(self.one_hot_to_categorical_mapping, self.domain_components):
      if component["var_type"] == CATEGORICAL_EXPERIMENT_PARAMETER_NAME:
        categorical_length_scales.append([one_hot_length_scales[index] for index in mapping["input_ind_value_map"]])
      else:
        categorical_length_scales.append([one_hot_length_scales[mapping["input_ind"]]])
    return categorical_length_scales

  def map_one_hot_points_to_categorical(self, one_hot_points, temperature=None):
    if self.is_integer_constrained:
      one_hot_points = self.snap_one_hot_points_to_integer_feasible(one_hot_points)
    if not (self.has_categoricals or self.has_quantized):
      return self.round_one_hot_points_integer_values(one_hot_points)

    temperature = max(temperature or DEFAULT_ONE_HOT_SNAPPING_TEMPERATURE, MINIMUM_ONE_HOT_SNAPPING_TEMPERATURE)

    def rel_prob_func(z):
      temp = numpy.power(z, 1 / temperature) + 1e-300  # A number near the smallest nonzero number on a computer
      return temp / sum(temp)

    categorical_points = []
    for one_hot_point in one_hot_points:
      assert len(one_hot_point) == self.one_hot_dim
      this_cat_point = [None] * self.dim
      for this_cat_dim_map in self.one_hot_to_categorical_mapping:
        if this_cat_dim_map["var_type"] == DOUBLE_EXPERIMENT_PARAMETER_NAME:
          this_cat_point[this_cat_dim_map["output_ind"]] = one_hot_point[this_cat_dim_map["input_ind"]]
        elif this_cat_dim_map["var_type"] == INT_EXPERIMENT_PARAMETER_NAME:
          this_cat_point[this_cat_dim_map["output_ind"]] = round(one_hot_point[this_cat_dim_map["input_ind"]])
        elif this_cat_dim_map["var_type"] == QUANTIZED_EXPERIMENT_PARAMETER_NAME:
          quantized_values = numpy.array(self.domain_components[this_cat_dim_map["output_ind"]]["elements"])
          nearest_idx = numpy.argmin(numpy.abs(one_hot_point[this_cat_dim_map["input_ind"]] - quantized_values))
          this_cat_point[this_cat_dim_map["output_ind"]] = quantized_values[nearest_idx]
        else:
          one_hot_indexes, categories = zip(*this_cat_dim_map["input_ind_value_map"].items())
          values = one_hot_point[numpy.array(one_hot_indexes, dtype=int)]
          this_cat_point[this_cat_dim_map["output_ind"]] = numpy.random.choice(categories, p=rel_prob_func(values))
      assert not any(p is None for p in this_cat_point)
      categorical_points.append(this_cat_point)
    return numpy.array(categorical_points, dtype=float)

  def round_one_hot_points_integer_values(self, one_hot_points):
    integer_component_mappings = self.get_integer_component_mappings()
    if len(integer_component_mappings) == 0:
      return one_hot_points

    snapped_points = numpy.copy(one_hot_points)
    for icm in integer_component_mappings:
      snapped_points[:, icm["input_ind"]] = numpy.round(snapped_points[:, icm["input_ind"]])
    return snapped_points

  def round_one_hot_points_quantized_values(self, one_hot_points):
    quantized_component_mappings = self.get_quantized_component_mappings()
    if len(quantized_component_mappings) == 0:
      return one_hot_points

    snapped_points = numpy.copy(one_hot_points)
    for qcm in quantized_component_mappings:
      quantized_values = numpy.array(self.domain_components[qcm["output_ind"]]["elements"])
      unrounded_values = snapped_points[:, qcm["input_ind"]]
      idxs = numpy.argmin(numpy.abs(unrounded_values[:, None] - quantized_values), axis=1)
      snapped_points[:, qcm["input_ind"]] = quantized_values[idxs]
    return snapped_points

  def round_one_hot_points_categorical_values(self, one_hot_points):
    categorical_component_mappings = self.get_categorical_component_mappings()
    if len(categorical_component_mappings) == 0:
      return one_hot_points

    categorical_component_mappings = self.get_categorical_component_mappings()
    snapped_points = numpy.copy(one_hot_points)
    for categorical_component_mapping in categorical_component_mappings:
      cat_indices = list(categorical_component_mapping["input_ind_value_map"])
      best_categories = numpy.argmax(one_hot_points[:, cat_indices], axis=1)
      snapped_points[:, cat_indices] = 0
      snapped_points[range(len(one_hot_points)), cat_indices[0] + best_categories] = 1
    return snapped_points

  def generate_feasible_integer_neighbors(self, one_hot_point):
    A, b = self.get_integer_one_hot_constraint_matrices()
    integer_neighbors = self.generate_integer_neighbors_for_integer_constraints(one_hot_point)

    # TODO(RTL-148): later, vectorize domain.check_point_satisfies_constraints to reuse it here
    feasible_neighbor_indices = numpy.all(numpy.dot(A, integer_neighbors.T) <= b[:, None], axis=0)
    return integer_neighbors[feasible_neighbor_indices]

  # TODO(RTL-149): Consider changing snapping behavior to be a little more consistent
  # (e.g., taking distance into account)
  def snap_one_hot_points_to_integer_feasible(self, one_hot_points):
    n_points = one_hot_points.shape[0]
    still_infeasible_indices = []
    feasible_padding_points = numpy.empty((0, one_hot_points.shape[1]))

    # For each point do nearest neighbor search, save a backup of feasible padding points for later use if needed.
    for i, one_hot_point in enumerate(one_hot_points):
      feasible_neighbors = self.generate_feasible_integer_neighbors(one_hot_point)
      numpy.random.shuffle(feasible_neighbors)
      if len(feasible_neighbors) > 0:
        one_hot_points[i] = feasible_neighbors[0]
        if len(feasible_padding_points) < n_points:
          num_padding_points = min(n_points - len(feasible_padding_points), len(feasible_neighbors) - 1)
          feasible_padding_points = numpy.vstack(
            [feasible_padding_points, feasible_neighbors[1 : num_padding_points + 1]]
          )
      else:
        still_infeasible_indices.append(i)

    # Pad out points for which we did not find a feasible neighbor
    if len(still_infeasible_indices) > 0 and len(feasible_padding_points) > 0:
      for feasible_neighbor, still_infeasible_idx in zip(feasible_padding_points, still_infeasible_indices):
        one_hot_points[still_infeasible_idx, :] = feasible_neighbor
      del still_infeasible_indices[: len(feasible_padding_points)]

    # return list with infeasible points removed
    one_hot_points_integer_feasible = numpy.delete(one_hot_points, still_infeasible_indices, axis=0)
    return one_hot_points_integer_feasible


class FixedIndicesOnContinuousDomain(object):
  def __init__(self, continuous_domain, fixed_indices):
    assert isinstance(continuous_domain, ContinuousDomain)
    assert isinstance(fixed_indices, dict)
    self.continuous_domain = continuous_domain
    self.fixed_indices = fixed_indices
    self._verify_fixed_indices()

  @property
  def dim(self):
    return self.continuous_domain.dim

  def _verify_fixed_indices(self):
    assert all(isinstance(k, int) for k in self.fixed_indices.keys())
    assert min(self.fixed_indices.keys()) >= 0
    assert max(self.fixed_indices.keys()) < self.continuous_domain.dim
    for index, value in self.fixed_indices.items():
      bound = self.continuous_domain.domain_bounds[index]
      assert bound[0] <= value <= bound[1]
      if self.continuous_domain.is_constrained:
        assert index in self.continuous_domain.one_hot_unconstrained_indices

  def _fix_points_according_to_fixed_indices(self, points):
    for index, value in self.fixed_indices.items():
      points[:, index] = value
    return points

  def generate_quasi_random_points_in_domain(self, num_points, log_sample=False):
    unfixed_points = self.continuous_domain.generate_quasi_random_points_in_domain(num_points, log_sample)
    return self._fix_points_according_to_fixed_indices(unfixed_points)

  def generate_random_points_near_point(self, num_points, point, std_dev, on_constraint=False):
    unfixed_points = self.continuous_domain.generate_random_points_near_point(
      num_points,
      point,
      std_dev,
      on_constraint,
    )
    return self._fix_points_according_to_fixed_indices(unfixed_points)

  def restrict_points_to_domain(self, points, on_constraint=False, viable_point=None):
    unfixed_points = self.continuous_domain.restrict_points_to_domain(points, on_constraint, viable_point)
    return self._fix_points_according_to_fixed_indices(unfixed_points)
