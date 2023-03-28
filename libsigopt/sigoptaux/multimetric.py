# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy


"""
This function takes advantage of numpy logical access: if you have
a = [1, 2, 3, 4] and you define a logical array ind = numpy.array([1, 0, 0, 1], dtype=bool)
a[ind] will return [1, 4].

It loops through each of the still-acceptable values (as checked with good_ind[i]) and then determines which
of the still-acceptable values are not dominated by the current values.  This computation of checking if
any metrics are dominated is checked with values[good_ind] >= c.  Then the checking if there are any metrics that
are not dominated is any(..., axis=1).  good_ind[good_ind] eliminated observations which are dominated.

This function assumes that the input `values` are being maximized.
For minimized metrics, the `values` must be negated before using this method.
"""


def find_pareto_frontier_observations_for_maximization(values, observations):
  values = numpy.array(values)
  observations = numpy.array(observations)
  assert len(values) == len(observations) and len(values.shape) == 2 and len(observations.shape) == 1
  assert not numpy.any(numpy.isnan(values))

  good_ind = numpy.ones(values.shape[0], dtype=bool)
  for i, c in enumerate(values):
    if good_ind[i]:
      good_ind[good_ind] = numpy.logical_or(
        numpy.all(values[good_ind] >= c, axis=1), numpy.any(values[good_ind] > c, axis=1)
      )

  return observations[good_ind].tolist(), observations[numpy.logical_not(good_ind)].tolist()
