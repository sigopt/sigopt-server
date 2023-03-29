# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from libsigopt.aux.geometry_utils import compute_distance_matrix_squared
from libsigopt.compute.search import convert_one_hot_to_search_hypercube_points
from libsigopt.compute.views.view import View


def k_center_clustering(points, first_center_index, k):
  assert len(points.shape) == 2
  assert 0 < k < points.shape[0]
  assert -1 < first_center_index < points.shape[0]
  distance_matrix_squared = numpy.zeros((k, len(points)))
  centers_indices = [first_center_index]
  furhest_point_index = first_center_index
  for i in range(k):
    last_center = points[furhest_point_index, None]
    distance_matrix_squared[i, :] = compute_distance_matrix_squared(last_center, points)
    distance_matrix_squared[i, furhest_point_index] = -numpy.inf
    if i == k - 1:
      break
    furhest_point_index = numpy.argmax(numpy.min(distance_matrix_squared[: i + 1, :], axis=0))
    centers_indices.append(furhest_point_index)
  partition = numpy.argmin(distance_matrix_squared, axis=0)
  return centers_indices, partition


class MultisolutionBestAssignments(View):
  view_name = "multisolution_best_assignments"

  def view(self):
    num_solutions = self.params["num_solutions"]
    assert num_solutions > 1
    assert not self.params["metrics_info"].requires_pareto_frontier_optimization
    values = self.points_sampled_for_af_values[:, 0]

    first_center_index = numpy.argmin(values)
    search_points = convert_one_hot_to_search_hypercube_points(self.domain, self.one_hot_points_sampled_points)
    _, partition = k_center_clustering(search_points, first_center_index, k=num_solutions)

    # Get the best index for each partition
    best_index_partition = [None] * num_solutions
    best_value_partition = [None] * num_solutions
    for i, p in enumerate(partition):
      if best_value_partition[p] is None or values[i] < best_value_partition[p]:
        best_value_partition[p] = values[i]
        best_index_partition[p] = i

    best_indices = best_index_partition
    assert all(isinstance(i, int) for i in best_indices)
    assert len(numpy.unique(best_indices)) == num_solutions
    assert min(best_indices) >= 0 and max(best_indices) <= len(search_points) - 1
    return {
      "endpoint": self.view_name,
      "best_indices": best_indices,
      "tag": self.tag,
    }
