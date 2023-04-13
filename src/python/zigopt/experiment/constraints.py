# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from zigopt.common.lists import *
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import PARAMETER_DOUBLE, PARAMETER_INT

from libsigopt.aux.constant import DOUBLE_EXPERIMENT_PARAMETER_NAME, INT_EXPERIMENT_PARAMETER_NAME, ConstraintType
from libsigopt.aux.geometry_utils import find_interior_point


CONSTRAINT_SYMBOL_MAP = {ConstraintType.greater_than: ">=", ConstraintType.less_than: "<="}


def human_readable_constraint(constraint):
  lhs = " + ".join([f"{term.coeff} * {term.name}" for term in constraint.terms])
  symbol = CONSTRAINT_SYMBOL_MAP[constraint.type]
  msg = f"{lhs} {symbol} {constraint.rhs}"
  return msg


class InfeasibleConstraintsError(Exception):
  def __init__(self, msg):
    super().__init__(msg)


@generator_to_list
def parse_experiment_constraints_to_func_list(experiment):
  # The linear coefficients assume that all the parameters are
  # continuous and they are sorted by name.

  dim = experiment.dimension
  parameter_list = experiment.all_parameters_sorted
  for constraint in experiment.constraints:
    nonzero_coef_map = {a.name: a.coeff for a in constraint.terms}
    constraint_vec = numpy.zeros(dim)
    var_type = None
    for index, p in enumerate(parameter_list):
      if p.name in nonzero_coef_map:
        constraint_vec[index] = nonzero_coef_map[p.name]
        if p.param_type == PARAMETER_DOUBLE:
          var_type = DOUBLE_EXPERIMENT_PARAMETER_NAME
        elif p.param_type == PARAMETER_INT:
          var_type = INT_EXPERIMENT_PARAMETER_NAME
        else:
          raise ValueError('Constraint must have "var_type" set to either "int" or "double"')

    # Invert less_than constrains
    assert constraint.type in (ConstraintType.greater_than, ConstraintType.less_than)
    sign = -1 if constraint.type == ConstraintType.less_than else 1

    weights = sign * constraint_vec
    rhs = sign * constraint.rhs
    yield {
      "weights": weights,
      "rhs": rhs,
      "var_type": var_type,
    }


def parse_constraints_to_list_of_constrained_parameter_names(constraints):
  constrained_variables: list = []
  for constraint in constraints:
    constrained_variables = constrained_variables + [term.name for term in constraint.terms]
  return list(set(constrained_variables))


def parse_constraints_to_halfspaces(constraints, parameters):
  """Generates a halfspaces matrix from the constraints and bounds.

    We follow scipy convention for halfspaces => Stacked Inequalities
    of the form Ax <= b in format [A; -b].

    """
  # pylint: disable=too-many-locals
  constrained_parameters_names = parse_constraints_to_list_of_constrained_parameter_names(constraints)
  constrained_parameters = [p for p in parameters if p.name in constrained_parameters_names]
  dim = len(constrained_parameters)
  num_explicit_constraints = len(constraints)
  n_halfspaces = 2 * dim + num_explicit_constraints
  halfspaces = numpy.zeros((n_halfspaces, dim + 1))

  for ic, constraint in enumerate(constraints):
    # Invert less_than constraints
    assert constraint.type in (ConstraintType.greater_than, ConstraintType.less_than)
    sign = -1 if constraint.type == ConstraintType.less_than else 1

    halfspaces[ic, -1] = sign * constraint.rhs
    nonzero_coef_map = {a.name: a.coeff for a in constraint.terms}
    for ip, p in enumerate(constrained_parameters):
      if p.name in nonzero_coef_map:
        halfspaces[ic, ip] = -sign * nonzero_coef_map[p.name]

  # TODO(RTL-152): Bounds as halfspaces. Check if those are correct
  for index, p in enumerate(constrained_parameters):
    imin = num_explicit_constraints + 2 * index
    imax = num_explicit_constraints + 2 * index + 1

    halfspaces[imin, -1] = p.bounds.minimum
    halfspaces[imax, -1] = -p.bounds.maximum
    halfspaces[imin, index] = -1
    halfspaces[imax, index] = 1

  return halfspaces


def has_feasible_constraints(experiment):
  if not experiment.constraints:
    return True

  for c in experiment.constraints:
    if numpy.sum([t.coeff != 0 for t in c.terms]) < 2:
      raise InfeasibleConstraintsError("Constraints should affect at least two parameters")

  halfspaces = experiment.halfspaces
  _, _, feasibility = find_interior_point(halfspaces)
  if not feasibility:
    raise InfeasibleConstraintsError("Infeasible constraints or empty set")
  return True
