# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy

import numpy

from libsigopt.compute.misc.constant import (
  AF_OPT_NEAR_BEST_STD_DEV,
  DEFAULT_MAX_SIMULTANEOUS_EI_POINTS,
  GRADIENT_BASED_OPTIMIZERS,
)
from libsigopt.compute.optimization_auxiliary import AdamParameters, DEParameters, OptimizerInfo
from libsigopt.compute.vectorized_optimizers import AdamOptimizer, DEOptimizer


DEFAULT_NEXT_POINTS_ES_OPTIMIZER_INFO = OptimizerInfo(
  optimizer=DEOptimizer,
  parameters=DEParameters(),
  num_multistarts=500,
  num_random_samples=10000,
)

DEFAULT_NEXT_POINTS_GB_OPTIMIZER_INFO = OptimizerInfo(
  optimizer=AdamOptimizer,
  parameters=AdamParameters(),
  num_multistarts=200,
  num_random_samples=50,
)

VECTORIZED_NEXT_POINTS_QEI_OPTIMIZER_INFO = OptimizerInfo(
  optimizer=DEOptimizer,
  parameters=DEParameters(),
  num_multistarts=100,
  num_random_samples=0,
)
VECTORIZED_NEXT_POINTS_QEI_FIXED_MAXITER = 250


"""
This function finds the maxiter for a vectorized optimizer given the dimension of the problem, the number of
multistarts, the number of points sampled. The look-up table values are computed using the default num_multistarts
(500 for ES, 200 for GB). The dimension of the look-up tables is (20, 15), where 20 corresponds to the
max number of dimensions, and 15 is number of 40-interval from [0, 600], the range of num_points_sampled for GPs

Then for a given dim=d, and num_points_sampled = n, we can get the iterations by performing
iteration_table[d - 1][(num_points_sampled - 1) // 40)]

On the smaller problems, we completely shut off gradient based (GB) optimizers, so the maxiters are 0

The maxiter numbers are selected here so that we can manage growth of the optimization time at a reasonable rate.
For example, in the most extreme case where d=20, n=600
The maximum ES optimizer runtime is ~2.65 s
The maximum GB optimizer runtime is ~4.71 s
So the total runtime is ~7 seconds per next point

Finally we also return the expected optimization time for this maxiter.
"""


def find_optimizer_maxiter(domain, acquisition_function, num_multistarts, optimizer_name):
  num_points_sampled_interval = 40
  # TODO(RTL-27): Revisit these iterations tables to improve efficiency.
  es_iteration_table = [
    [499, 252, 232, 190, 167, 153, 143, 136, 131, 126, 123, 120, 118, 116, 114],
    [467, 248, 231, 189, 167, 153, 143, 136, 130, 126, 123, 120, 118, 116, 114],
    [440, 245, 229, 189, 167, 152, 143, 136, 130, 126, 123, 120, 118, 116, 114],
    [416, 241, 228, 188, 166, 152, 143, 136, 130, 126, 123, 120, 118, 115, 114],
    [395, 238, 227, 187, 166, 152, 143, 136, 130, 126, 123, 120, 117, 115, 114],
    [376, 235, 225, 187, 165, 152, 142, 135, 130, 126, 123, 120, 117, 115, 114],
    [359, 232, 224, 186, 165, 152, 142, 135, 130, 126, 123, 120, 117, 115, 114],
    [343, 230, 223, 186, 165, 151, 142, 135, 130, 126, 123, 120, 117, 115, 114],
    [329, 227, 221, 185, 164, 151, 142, 135, 130, 126, 123, 120, 117, 115, 114],
    [317, 225, 220, 184, 164, 151, 142, 135, 130, 126, 122, 120, 117, 115, 114],
    [305, 222, 219, 184, 164, 151, 142, 135, 130, 126, 122, 120, 117, 115, 114],
    [294, 219, 218, 183, 163, 151, 142, 135, 130, 126, 122, 120, 117, 115, 114],
    [285, 217, 217, 183, 163, 150, 141, 135, 130, 126, 122, 120, 117, 115, 114],
    [275, 215, 215, 182, 163, 150, 141, 135, 130, 126, 122, 120, 117, 115, 114],
    [267, 214, 214, 181, 162, 150, 141, 135, 130, 126, 122, 120, 117, 115, 114],
    [259, 213, 213, 181, 162, 150, 141, 134, 129, 125, 122, 120, 117, 115, 114],
    [252, 212, 212, 180, 162, 149, 141, 134, 129, 125, 122, 120, 117, 115, 114],
    [245, 211, 211, 180, 161, 149, 141, 134, 129, 125, 122, 119, 117, 115, 114],
    [239, 210, 210, 179, 161, 149, 141, 134, 129, 125, 122, 119, 117, 115, 114],
    [233, 209, 209, 179, 161, 149, 140, 134, 129, 125, 122, 119, 117, 115, 114],
  ]
  ES_ITERATIONS_BEYOND_TABLE = 100
  gd_iteration_table = [
    [0, 0, 0, 118, 105, 97, 92, 88, 85, 82, 80, 79, 78, 76, 75],
    [0, 0, 0, 114, 102, 95, 90, 86, 83, 81, 79, 77, 76, 75, 74],
    [0, 0, 0, 110, 99, 92, 88, 84, 81, 79, 78, 76, 75, 74, 73],
    [0, 0, 0, 107, 97, 90, 86, 83, 80, 78, 77, 75, 74, 73, 73],
    [0, 0, 0, 105, 95, 89, 84, 81, 79, 77, 76, 74, 73, 73, 72],
    [0, 0, 120, 102, 93, 87, 83, 80, 78, 76, 75, 74, 73, 72, 71],
    [0, 0, 117, 100, 91, 86, 82, 79, 77, 75, 74, 73, 72, 71, 71],
    [0, 0, 114, 98, 90, 84, 81, 78, 76, 75, 73, 72, 72, 71, 70],
    [0, 0, 112, 96, 88, 83, 80, 77, 75, 74, 73, 72, 71, 70, 70],
    [0, 0, 110, 95, 87, 82, 79, 77, 75, 73, 72, 71, 71, 70, 69],
    [0, 0, 108, 93, 86, 81, 78, 76, 74, 73, 72, 71, 70, 70, 69],
    [0, 0, 106, 92, 85, 80, 77, 75, 74, 72, 71, 71, 70, 69, 69],
    [0, 0, 104, 91, 84, 80, 77, 75, 73, 72, 71, 70, 70, 69, 68],
    [0, 0, 103, 90, 83, 79, 76, 74, 73, 72, 71, 70, 69, 69, 68],
    [0, 0, 101, 89, 82, 78, 76, 74, 72, 71, 70, 70, 69, 68, 68],
    [0, 0, 100, 88, 82, 78, 75, 73, 72, 71, 70, 69, 69, 68, 68],
    [0, 0, 99, 87, 81, 77, 75, 73, 72, 71, 70, 69, 68, 68, 67],
    [0, 0, 97, 86, 80, 77, 74, 73, 71, 70, 69, 69, 68, 68, 67],
    [0, 0, 96, 85, 80, 76, 74, 72, 71, 70, 69, 68, 68, 68, 67],
    [0, 0, 95, 85, 79, 76, 73, 72, 71, 70, 69, 68, 68, 67, 67],
  ]
  GD_ITERATIONS_BEYOND_TABLE = 50
  if optimizer_name in GRADIENT_BASED_OPTIMIZERS:
    assert num_multistarts == DEFAULT_NEXT_POINTS_GB_OPTIMIZER_INFO.num_multistarts
    iteration_table = gd_iteration_table
  else:
    assert num_multistarts == DEFAULT_NEXT_POINTS_ES_OPTIMIZER_INFO.num_multistarts
    iteration_table = es_iteration_table

  dim = domain.dim
  num_points_sampled = len(acquisition_function.predictor.points_sampled)

  if dim > len(iteration_table) or num_points_sampled > len(iteration_table[0]) * num_points_sampled_interval:
    maxiter = GD_ITERATIONS_BEYOND_TABLE if optimizer_name in GRADIENT_BASED_OPTIMIZERS else ES_ITERATIONS_BEYOND_TABLE
  else:
    # dim and num_points_sampled are 1 indexed.
    maxiter = iteration_table[dim - 1][(num_points_sampled - 1) // num_points_sampled_interval]

  return maxiter


def qei_acquisition_function_optimization(
  domain,
  acquisition_function,
):
  qei_optimizer = VECTORIZED_NEXT_POINTS_QEI_OPTIMIZER_INFO.optimizer(
    domain=domain,
    acquisition_function=acquisition_function,
    num_multistarts=VECTORIZED_NEXT_POINTS_QEI_OPTIMIZER_INFO.num_multistarts,
    maxiter=VECTORIZED_NEXT_POINTS_QEI_FIXED_MAXITER,
  )
  next_points, _ = qei_optimizer.optimize()
  return (
    next_points,
    VECTORIZED_NEXT_POINTS_QEI_OPTIMIZER_INFO,
  )


def constant_liar_acquisition_function_optimization(
  domain,
  acquisition_function,
  num_to_sample,
):
  af = copy.deepcopy(acquisition_function)
  next_points = []
  es_maxiter = find_optimizer_maxiter(
    domain=domain,
    acquisition_function=af,
    num_multistarts=DEFAULT_NEXT_POINTS_ES_OPTIMIZER_INFO.num_multistarts,
    optimizer_name=DEFAULT_NEXT_POINTS_ES_OPTIMIZER_INFO.optimizer.optimizer_name,
  )
  gd_maxiter = find_optimizer_maxiter(
    domain=domain,
    acquisition_function=af,
    num_multistarts=DEFAULT_NEXT_POINTS_GB_OPTIMIZER_INFO.num_multistarts,
    optimizer_name=DEFAULT_NEXT_POINTS_GB_OPTIMIZER_INFO.optimizer.optimizer_name,
  )
  pretest_locations = domain.generate_quasi_random_points_in_domain(
    DEFAULT_NEXT_POINTS_ES_OPTIMIZER_INFO.num_random_samples
  )

  for _ in range(num_to_sample):
    es_af_optimizer = DEFAULT_NEXT_POINTS_ES_OPTIMIZER_INFO.optimizer(
      domain=domain,
      acquisition_function=af,
      num_multistarts=DEFAULT_NEXT_POINTS_ES_OPTIMIZER_INFO.num_multistarts,
      optimizer_parameters=DEFAULT_NEXT_POINTS_ES_OPTIMIZER_INFO.parameters,
      maxiter=es_maxiter,
    )
    gd_af_optimizer = DEFAULT_NEXT_POINTS_GB_OPTIMIZER_INFO.optimizer(
      domain=domain,
      acquisition_function=af,
      num_multistarts=DEFAULT_NEXT_POINTS_GB_OPTIMIZER_INFO.num_multistarts,
      optimizer_parameters=DEFAULT_NEXT_POINTS_GB_OPTIMIZER_INFO.parameters,
      maxiter=gd_maxiter,
    )
    next_point = vectorized_acquisition_optimization(es_af_optimizer, gd_af_optimizer, pretest_locations)
    assert next_point.shape == (af.dim,)
    af.append_lie_locations(numpy.atleast_2d(next_point))
    next_points.append(next_point)
  optimizer_info_dict = {
    "es_optimizer": repr(es_af_optimizer),
    "gd_optimizer": repr(gd_af_optimizer),
  }
  return numpy.array(next_points), optimizer_info_dict


def vectorized_acquisition_optimization(es_af_optimizer, gd_af_optimizer, pretest_locations):
  random_af_values = es_af_optimizer.af.evaluate_at_point_list(
    pretest_locations,
    batch_size=DEFAULT_MAX_SIMULTANEOUS_EI_POINTS,
  )
  best_af_location = pretest_locations[numpy.argmax(random_af_values), :]
  best_observed_location = es_af_optimizer.af.best_location

  best_es_result, all_es_results = es_af_optimizer.optimize(numpy.vstack((best_af_location, best_observed_location)))
  random_near_best_es_result = es_af_optimizer.domain.generate_random_points_near_point(
    DEFAULT_NEXT_POINTS_GB_OPTIMIZER_INFO.num_random_samples,
    best_es_result,
    AF_OPT_NEAR_BEST_STD_DEV,
  )
  random_es_results = all_es_results.ending_points[
    numpy.random.choice(
      es_af_optimizer.num_multistarts,
      DEFAULT_NEXT_POINTS_GB_OPTIMIZER_INFO.num_random_samples,
      replace=False,
    )
  ]
  # Use a combination of points near the ES solution and random
  # ES solutions for the starting point of the gradient method
  gd_starting_points = numpy.concatenate(
    (
      random_near_best_es_result,
      random_es_results,
    )
  )
  assert len(gd_starting_points) <= gd_af_optimizer.num_multistarts
  best_point, _ = gd_af_optimizer.optimize(selected_starts=gd_starting_points)
  return best_point
