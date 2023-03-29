# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy

import numpy

from libsigopt.compute.covariance import C4RadialMatern
from libsigopt.compute.sigopt_parzen_estimator import SigOptParzenEstimator
from libsigopt.compute.views.rest.search_next_points import (
  SEARCH_EXPLOITATION_PHASE,
  SEARCH_EXPLORE_RESOLVE_PHASE,
  SEARCH_INITIALIZATION_PHASE,
  identify_search_phase,
)
from libsigopt.compute.views.rest.spe_next_points import SPE_CAT_LENGTH_SCALE, SPENextPoints
from libsigopt.compute.views.view import View, identify_scaled_values_exceeding_scaled_upper_thresholds


class SPESearchNextPoints(View):
  view_name = "spe_search_next_points"

  def initilization_sequence(self):
    num_to_sample = self.params["num_to_sample"]
    if self.domain.priors and not self.domain.constraint_list:
      suggested_points = self.domain.generate_random_points_according_to_priors(num_to_sample)
    else:
      suggested_points = self.domain.generate_quasi_random_points_in_domain(num_to_sample)
    results = {
      "endpoint": self.view_name,
      "points_to_sample": suggested_points,
      "tag": self.tag,
    }
    return results

  def single_metric_spe_next_points(self):
    optimized_metric = numpy.random.choice(self.constraint_metrics_index)
    view_input = deepcopy(self.params)
    view_input["metrics_info"].optimized_metrics_index = [optimized_metric]
    view_input["metrics_info"].constraint_metrics_index = []
    return SPENextPoints(view_input).view()

  def metric_constraints_spe_next_points(self):
    if len(self.constraint_metrics_index) == 1:
      return self.single_metric_spe_next_points()
    optimized_metric = numpy.random.choice(self.constraint_metrics_index)
    constraint_metrics = [i for i in self.params["metrics_info"].constraint_metrics_index if i != optimized_metric]
    view_input = deepcopy(self.params)
    view_input["metrics_info"].optimized_metrics_index = [optimized_metric]
    view_input["metrics_info"].constraint_metrics_index = constraint_metrics
    return SPENextPoints(view_input).view()

  def form_sigopt_parzen_estimator_for_search(
    self,
    one_hot_points_sampled_points,
    points_sampled_values,
  ):
    lower_covariance_factor = 2.0
    greater_covariance_factor = 5.0
    gamma = 0.2

    temp_covariance = C4RadialMatern([1.0] * (1 + self.domain.one_hot_dim))
    spe = SigOptParzenEstimator(
      lower_covariance=temp_covariance,
      greater_covariance=temp_covariance,
      points_sampled_points=one_hot_points_sampled_points,
      points_sampled_values=points_sampled_values,
      gamma=gamma,
      forget_factor=0,
    )
    metric_constraints_violations = identify_scaled_values_exceeding_scaled_upper_thresholds(
      self.points_sampled_for_pf_values,
      self.constraint_thresholds,
    )
    # HACK: Manually force the split of lower and greater points based on user thresholds
    observation_count, dim = one_hot_points_sampled_points.shape
    if observation_count - sum(metric_constraints_violations) > dim:
      spe.lower_points = one_hot_points_sampled_points[~metric_constraints_violations]
      spe.greater_points = one_hot_points_sampled_points[metric_constraints_violations]
      spe.gamma = sum(metric_constraints_violations) / len(metric_constraints_violations)
    lower_covariance = SPENextPoints.form_one_hot_covariance(
      C4RadialMatern,
      self.domain,
      spe.lower_points,
      SPE_CAT_LENGTH_SCALE,
      lower_covariance_factor,
    )
    greater_covariance = SPENextPoints.form_one_hot_covariance(
      C4RadialMatern,
      self.domain,
      spe.greater_points,
      SPE_CAT_LENGTH_SCALE,
      greater_covariance_factor,
    )
    spe.update_covariances(lower_covariance, greater_covariance)
    return spe

  def spe_search_next_points(self):
    num_to_sample = self.params["num_to_sample"]
    random_pf_metric_index = numpy.random.choice(len(self.constraint_metrics_index))
    sigopt_parzen_estimator = self.form_sigopt_parzen_estimator_for_search(
      self.one_hot_points_sampled_points,
      self.points_sampled_for_pf_values[:, random_pf_metric_index],
    )
    oh_suggested_points, _, _, _ = SPENextPoints.draw_samples(
      sigopt_parzen_estimator,
      num_to_sample,
      self.domain,
      proposal_std=0.1,
    )
    suggested_points = self.domain.map_one_hot_points_to_categorical(oh_suggested_points)
    return suggested_points

  def get_search_phase(self):
    observation_budget = self.params["metrics_info"].observation_budget
    observation_count = len(self.params["points_sampled"].points)
    num_open_suggestions = len(self.one_hot_points_being_sampled_points)
    failure_count = numpy.sum(self.params["points_sampled"].failures)
    return identify_search_phase(
      observation_budget,
      observation_count,
      num_open_suggestions,
      failure_count,
    )

  def view(self):
    assert self.has_constraint_metrics
    assert not self.has_optimization_metrics
    search_phase = self.get_search_phase()

    if search_phase is SEARCH_INITIALIZATION_PHASE:
      return self.initilization_sequence()
    elif search_phase is SEARCH_EXPLOITATION_PHASE:
      return self.metric_constraints_spe_next_points()

    assert search_phase is SEARCH_EXPLORE_RESOLVE_PHASE
    proposed_next_points = self.spe_search_next_points()

    results = {
      "endpoint": self.view_name,
      "points_to_sample": proposed_next_points,
      "tag": self.tag,
    }
    return results
