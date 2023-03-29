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
from libsigopt.aux.geometry_utils import compute_distance_matrix_squared
from libsigopt.compute.domain import CategoricalDomain
from libsigopt.compute.search import convert_one_hot_to_search_hypercube_points
from libsigopt.compute.views.rest.multisolution_best_assignments import k_center_clustering
from testcompute.zigopt_input_utils import form_random_unconstrained_categorical_domain


class TestMultisolutionBestAssignments(object):
  def test_k_center_clustering_invalid_input_points(self):
    points = numpy.random.randn(20)
    with pytest.raises(AssertionError):
      k_center_clustering(points, first_center_index=0, k=10)

    points = numpy.random.randn(20, 2, 1)
    with pytest.raises(AssertionError):
      k_center_clustering(points, first_center_index=0, k=10)

  def test_k_center_clustering_invalid_input_k(self):
    for k in [-1, 0, 3, 50]:
      with pytest.raises(AssertionError):
        k_center_clustering(numpy.random.randn(3, 2), first_center_index=0, k=k)

  def test_k_center_clustering_invalid_input_first_center_index(self):
    for i in [-2, -1, 10, 27]:
      with pytest.raises(AssertionError):
        k_center_clustering(numpy.random.randn(10, 2), first_center_index=i, k=3)

  def test_k_center_clustering_categoricals(self):
    domain_components = [
      {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": [0, 2]},
      {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": [3, 8]},
      {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": [1, 5]},
    ]
    domain = CategoricalDomain(domain_components)

    num_points_a = 13
    center_cluster_a = numpy.array([1.9, 7.4, 0.1, 0.9])
    points_a = domain.one_hot_domain.generate_random_points_near_point(num_points_a, center_cluster_a, std_dev=0.01)

    num_points_b = 21
    center_cluster_b = numpy.array([0.1, 4, 0.9, 0.1])
    points_b = domain.one_hot_domain.generate_random_points_near_point(num_points_b, center_cluster_b, std_dev=0.01)

    points = numpy.concatenate((points_a, points_b))
    first_center_index = 3
    k = 2
    search_points = convert_one_hot_to_search_hypercube_points(domain, points)
    centers_indices, partition = k_center_clustering(search_points, first_center_index, k)

    assert len(centers_indices) == k
    assert centers_indices[0] < num_points_a  # indices of points a
    assert centers_indices[1] >= num_points_a  # indices of points b
    assert numpy.all(points[centers_indices[0], :] == points[first_center_index, :])  # must be the first center index
    assert numpy.all(partition[:num_points_a] == 0)
    assert numpy.all(partition[num_points_a:] == 1)

  @pytest.mark.parametrize("dim", [1, 2, 5, 7, 51])
  @pytest.mark.parametrize(
    "num_points, k",
    [
      (2, 1),
      (3, 2),
      (5, 1),
      (17, 16),
      (23, 7),
      (100, 21),
    ],
  )
  def test_k_center_clustering_random_points(self, dim, num_points, k):
    points = numpy.random.randn(num_points, dim)
    first_center_index = numpy.random.randint(num_points)
    centers_indices, partition = k_center_clustering(points, first_center_index, k)
    assert centers_indices[0] == first_center_index
    assert len(centers_indices) == k
    assert len(numpy.unique(partition)) == k
    assert numpy.all(partition[centers_indices] == range(k))

    distance_matrix_squared = compute_distance_matrix_squared(points[centers_indices], points)
    expected_partition = numpy.argmin(distance_matrix_squared, axis=0)
    assert numpy.all(expected_partition == partition)
    for i, c in enumerate(centers_indices):
      assert numpy.isclose(distance_matrix_squared[i, c], 0.0)

  def test_k_center_clustering_same_points(self):
    num_points = 12
    k = 4
    repeated_point = numpy.array([[1, 1, 1]])
    points = numpy.repeat(repeated_point, num_points, axis=0)
    point_far_away = numpy.array([[9, 9, 9]])
    index_far_away = 3
    points[index_far_away, :] = point_far_away

    first_center_index = 4
    centers_indices, partition = k_center_clustering(points, first_center_index, k)

    assert centers_indices == [first_center_index, index_far_away, 0, 1]
    assert partition[first_center_index] == 0  # first cluster
    assert partition[index_far_away] == 1  # second cluster
    assert partition[0] == 2  # third cluster
    assert partition[1] == 3  # forth cluster
    remaining_repeated_elements = [i for i in range(num_points) if i not in centers_indices]
    assert all(partition[i] == 0 for i in remaining_repeated_elements)

  @pytest.mark.parametrize("dim", [1, 2, 5, 7, 25])
  @pytest.mark.parametrize(
    "num_points, k",
    [
      (2, 1),
      (3, 2),
      (5, 3),
      (17, 16),
      (21, 2),
      (100, 20),
    ],
  )
  def test_k_center_clustering_same_points_random(self, dim, num_points, k):
    point = numpy.random.randn(1, dim)
    points = numpy.repeat(point, num_points, axis=0)

    first_center_index = numpy.random.randint(num_points)
    centers_indices, partition = k_center_clustering(points, first_center_index, k)
    assert centers_indices[0] == first_center_index
    assert len(centers_indices) == k
    assert len(numpy.unique(partition)) == k
    assert numpy.all(partition[centers_indices] == range(k))

  @pytest.mark.parametrize("categorical_dim", [1, 2, 5, 19, 21])
  @pytest.mark.parametrize("num_clusters", [1, 2, 4, 13])
  @pytest.mark.parametrize("num_points_per_clusters", [1, 3, 5, 11, 16])
  @pytest.mark.parametrize("sigma", [1e-5, 1e-1, 1, 1e2])
  def test_k_center_clustering_optimality(self, categorical_dim, num_clusters, num_points_per_clusters, sigma):
    domain = form_random_unconstrained_categorical_domain(categorical_dim)
    cluster_centers = domain.one_hot_domain.generate_quasi_random_points_in_domain(num_clusters)
    dim = domain.one_hot_domain.dim

    points = numpy.copy(cluster_centers)
    for i in range(num_clusters):
      curr_points = numpy.random.multivariate_normal(
        cluster_centers[i, :],
        sigma * numpy.eye(dim),
        num_points_per_clusters,
      )
      points = numpy.concatenate((points, curr_points))
    assert points.shape == (num_clusters * num_points_per_clusters + num_clusters, dim)

    shuffle_indices = numpy.random.permutation(len(points))
    optimal_centers_indices = [numpy.flatnonzero(shuffle_indices == i)[0] for i in range(num_clusters)]
    shuffled_points = points[shuffle_indices, :]
    assert numpy.allclose(shuffled_points[optimal_centers_indices, :], cluster_centers)

    first_center_index = numpy.random.randint(shuffled_points.shape[0])
    centers_indices, partition = k_center_clustering(shuffled_points, first_center_index, num_clusters)
    assert centers_indices[0] == first_center_index
    assert len(centers_indices) == num_clusters
    assert len(numpy.unique(partition)) == num_clusters
    assert numpy.all(partition[centers_indices] == range(num_clusters))

    distance_matrix_squared = compute_distance_matrix_squared(shuffled_points[centers_indices], shuffled_points)
    expected_partition = numpy.argmin(distance_matrix_squared, axis=0)
    assert numpy.allclose(expected_partition, partition)

    # k-center cluster must give us an 2-OPT approximation ratio
    largest_radius = numpy.sqrt(numpy.max(numpy.min(distance_matrix_squared, axis=0)))
    optimal_distance_matrix_squared = compute_distance_matrix_squared(
      shuffled_points[optimal_centers_indices],
      shuffled_points,
    )
    optimal_r = numpy.sqrt(numpy.max(numpy.min(optimal_distance_matrix_squared, axis=0)))
    assert largest_radius <= 2 * optimal_r
