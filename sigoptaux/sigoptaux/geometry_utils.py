# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
from scipy.optimize import linprog


MINIMUM_ACCEPTABLE_RADIUS = 1e-8


def find_interior_point(halfspaces):
  """Finds the Chebyshev center of a polytope defined as halfspaces.

    The Chebyshev center is the center of the largest hypersphere
    inscribed in the polytope. We formulate this as an LP

    min -r
    s.t. A_i^T x + norm(A_i) r  <= b_i, for all i in rows of A
    r >= 0

    If the center cannot be found, it represents that the constraints are infeasible.
    Returns: the center point, the radius of the hypersphere and a boolean indicating the
    feasibility of the constraints.

    """

  norm_vector = numpy.linalg.norm(halfspaces[:, :-1], axis=1)
  c = numpy.zeros(halfspaces.shape[1])
  c[-1] = -1
  A = numpy.copy(halfspaces)
  A[:, -1] = norm_vector
  b = -halfspaces[:, -1]
  bounds = [(None, None)] * (halfspaces.shape[1] - 1) + [(0, None)]
  res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs-ipm")
  if res.success:
    center = res.x[:-1]
    radius = res.x[-1]
    feasible = not (res.status == 2 or radius < MINIMUM_ACCEPTABLE_RADIUS)
  else:
    center = None
    radius = 0
    feasible = False

  return center, radius, feasible


def compute_distance_matrix_squared(x, z):
  assert x.shape[1] == z.shape[1]
  sum_x_sq = numpy.sum(x**2, axis=1)[:, None]
  sum_z_sq = numpy.sum(z**2, axis=1)[None, :]
  return numpy.fmax(0, sum_x_sq + sum_z_sq - 2 * numpy.dot(x, z.T))
