# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
import qmcpy

from libsigopt.aux.geometry_utils import find_interior_point


DEFAULT_REJECTION_SAMPLING_TRIALS = 1000000
REJECTION_SAMPLING_BLOCK_SIZE = 10000


def _verify_bounds(domain_bounds):
  return (
    len(domain_bounds.shape) == 2 and domain_bounds.shape[1] == 2 and numpy.all(numpy.diff(domain_bounds, axis=1) >= 0)
  )


def unit_cube_sampler_transform_decorator(unit_cube_generator):
  def wrapper(num_points, domain_bounds, skip=0, seed=None):
    assert _verify_bounds(domain_bounds)
    dimension = len(domain_bounds)
    if num_points == 0:
      return numpy.empty((0, dimension))
    unit_cube_points = unit_cube_generator(num_points, dimension, skip, seed)
    pts_scale = numpy.diff(domain_bounds, axis=1).ravel()
    pts_min = domain_bounds[:, 0]
    return pts_min + pts_scale * unit_cube_points

  return wrapper


@unit_cube_sampler_transform_decorator
def generate_uniform_random_points(num_points, dimension, skip, seed):
  return numpy.random.random((num_points, dimension))


def generate_uniform_random_points_rejection_sampling(num_points, domain_bounds, A, b, rejection_count=None):
  """Compute a set of uniform random points inside some linear constrained domain. Returns a set of feasible points and
    a bool, which is true if rejection sampling succeeded and false if it failed to find the sufficient points"""
  assert _verify_bounds(domain_bounds)
  if not rejection_count:
    rejection_count = DEFAULT_REJECTION_SAMPLING_TRIALS

  if num_points > 0:
    points = numpy.empty((0, len(domain_bounds)))
    left_points = num_points

    while (left_points > 0) and (rejection_count > 0):
      test_points = generate_uniform_random_points(REJECTION_SAMPLING_BLOCK_SIZE, domain_bounds)
      indexes = numpy.all(numpy.dot(A, test_points.T) <= b[:, None], axis=0)
      points = numpy.vstack((points, test_points[indexes, :]))
      left_points -= numpy.sum(indexes)
      rejection_count -= REJECTION_SAMPLING_BLOCK_SIZE

    if left_points > 0:
      return points, False
    else:
      return points[:num_points, :], True
  else:
    return numpy.empty((0, len(domain_bounds))), False


def generate_uniform_random_points_rejection_sampling_with_hitandrun_padding(num_points, domain_bounds, A, b, x0=None):
  points, success = generate_uniform_random_points_rejection_sampling(num_points, domain_bounds, A, b)
  if not success and num_points > 0:  # fill in rest with hitandrun if rejection fails

    if x0 is None:
      halfspaces = numpy.hstack((A, -b[:, None]))
      x0, _, _ = find_interior_point(halfspaces)

    num_points_identified = points.shape[0]
    num_points_remaining = num_points - num_points_identified
    points_remaining = generate_hitandrun_random_points(num_points_remaining, x0, A, b)
    points = numpy.vstack((points, points_remaining))
  return points, success


def generate_hitandrun_random_points(num_points, x0, A, b):
  """Compute a set of random points inside a polytope defined as Ax <= b.

      # Artificial Centering Hit and run
      # Kaufman, David E. and Smith, Robert L., "Direction Choice for
      # Accelerated Convergence in Hit-and-Run Sampling", Op. Res. 46,
      # pp. 84-95.

    :param num_points: number of random points to generate
    :type num_points: int > 0
    """

  def _gen_random_directions(dim, num_points):
    z = numpy.random.randn(num_points, dim)
    return z / numpy.linalg.norm(z, axis=1)[:, None]

  n_const, n_dim = A.shape
  assert n_const == len(b)

  # Number of samples with standard hit-and-run for initialization.
  runup = 10 * (n_dim + 1)
  # Number of samples to be discarded to avoid initial bias.
  discard = 25 * (n_dim + 1)

  # Initialize variables for keeping track of sample mean
  incremental_mean = numpy.zeros(n_dim)
  total_num_points = runup + discard + num_points
  points = numpy.zeros((total_num_points, n_dim))
  random_directions = _gen_random_directions(n_dim, total_num_points)
  uniform_rvs = numpy.random.rand(total_num_points)
  x = x0

  for iteration in range(total_num_points):
    # select random direction during runup phase
    if iteration < runup:
      direction = random_directions[iteration]
    else:
      # choose a previous point at random
      rpoint = points[numpy.random.choice(iteration), :]
      # line sampling direction is from v to sample mean
      norm_value = numpy.linalg.norm(rpoint - incremental_mean)
      if norm_value > 0.0:
        direction = (rpoint - incremental_mean) / norm_value
      else:
        direction = random_directions[iteration]

    # determine intersections of x + direction * t with the polytope
    z = numpy.dot(A, direction)
    c = (b - numpy.dot(A, x)) / z

    cmin = c[z < 0.0]
    cmax = c[z > 0.0]
    tmin = numpy.amax(cmin)
    tmax = numpy.amin(cmax)

    # choose a point on that line segment
    x = x + (tmin + (tmax - tmin) * uniform_rvs[iteration]) * direction
    points[iteration, :] = x
    incremental_mean = incremental_mean + (x - incremental_mean) / (iteration + 1)

  return points[(discard + runup) :]


@unit_cube_sampler_transform_decorator
def generate_latin_hypercube_points(num_points, dimension, skip, seed):
  points = numpy.linspace(0, 1, num_points, endpoint=False)
  points = points[:, None] + numpy.random.uniform(0.0, 1 / num_points, size=(num_points, dimension))
  for i in range(dimension):
    numpy.random.shuffle(points[:, i])
  return points


@unit_cube_sampler_transform_decorator
def generate_halton_points(num_points, dimension, skip, seed):
  halton = qmcpy.Halton(dimension=dimension, generalize=True, randomize=True, seed=seed)
  return halton.gen_samples(n_min=skip, n_max=skip + num_points)


@unit_cube_sampler_transform_decorator
def generate_sobol_points(num_points, dimension, skip, seed):
  sobol = qmcpy.Sobol(dimension=dimension, randomize="LMS", graycode=True, seed=seed)
  return sobol.gen_samples(n_min=skip, n_max=skip + num_points)


def generate_grid_points(points_per_dimension, domain_bounds):
  assert _verify_bounds(domain_bounds)
  points_per_dimension = numpy.asarray(points_per_dimension)
  if points_per_dimension.size == 0 or not points_per_dimension.all():
    return numpy.empty((0, len(domain_bounds)))

  if points_per_dimension.size == 1:
    points_per_dimension = numpy.resize(points_per_dimension, len(domain_bounds))

  per_axis_grid = [
    numpy.linspace(bounds[0], bounds[1], points_per_dimension[i]) for i, bounds in enumerate(domain_bounds)
  ]
  mesh_grid = numpy.meshgrid(*per_axis_grid)
  return numpy.vstack([numpy.ravel(g) for g in mesh_grid]).T
