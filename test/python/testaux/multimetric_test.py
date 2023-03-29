# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from libsigopt.aux.multimetric import find_pareto_frontier_observations_for_maximization


class TestMultimetric(object):
  def test_find_pareto_frontier_observations_for_maximization(self):
    values = [[0, 1], [1, 2], [3, 4], [4, 3]]
    observations = [0, 1, 2, 3]
    pf, npf = find_pareto_frontier_observations_for_maximization(values, observations)
    assert set(pf) == {2, 3} and set(npf) == {0, 1}

  def test_exclude_repeated_values_from_pareto_frontier(self):
    values = [[0, 1], [0, 2], [0, 3], [4, 2], [5, 2], [6, 1]]
    observations = [0, 1, 2, 3, 4, 5]
    pf, npf = find_pareto_frontier_observations_for_maximization(values, observations)
    assert set(pf) == {2, 4, 5} and set(npf) == {0, 1, 3}
