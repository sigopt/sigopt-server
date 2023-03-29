# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy

import numpy

from libsigopt.aux.constant import CATEGORICAL_EXPERIMENT_PARAMETER_NAME
from libsigopt.compute.covariance import C4RadialMatern
from libsigopt.compute.covariance_base import HyperparameterInvalidError
from libsigopt.compute.misc.constant import MULTIMETRIC_MIN_NUM_IN_BOUNDS_POINTS, MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS
from libsigopt.compute.misc.multimetric import filter_multimetric_points_sampled_spe
from libsigopt.compute.optimization import LBFGSBOptimizer, MultistartOptimizer, SLSQPOptimizer
from libsigopt.compute.sigopt_parzen_estimator import SigOptParzenEstimator, SPEInsufficientDataError
from libsigopt.compute.views.rest.gp_next_points_categorical import select_random_task_by_softmax
from libsigopt.compute.views.view import View, identify_scaled_values_exceeding_scaled_upper_thresholds


# SPE Phases
INITIALIZATION_PHASE = object()
SKO_PHASE = object()
COMPLETION_PHASE = object()

# When a customer did not give a budget, this times the dimension will be used as the budget for the SPE method
SPE_PHANTOM_BUDGET_FACTOR = 50

# NOTE: To increase this beyond 0, we would need to ensure that the observations
# are coming in to this method in increasing order by Observation ID - otherwise we would
# be forgetting points arbitrarily instead of forgetting the oldest points. Since this feature
# is currently unused we do not implement the required sort
MAX_FORGET_FACTOR = 0.0

SKO_PHASE_LIMIT = 0.75
TOP_GAMMA = 0.1
BOTTOM_GAMMA = 0.06
MINIMUM_SUCCESS_THRESHOLD = 0.1
INITIALIZATION_PHASE_LIMIT = 0.15

SPE_CAT_LENGTH_SCALE = 0.3
SPE_OPEN_SUGGESTION_RATIO_BOUND = 1.7
SPE_NUM_MULTISTARTS = 20
SPE_BATCH_SIZE = 1000
SPE_REJECTION_SAMPLES_LIMIT = 100000

# TODO(RTL-118): Eventually, we want to deal with the proposal distribution in a much cleaner way,
# this is a temporary fix that allows SPE to exploit during COMPLETION_PHASE
SPE_PROPOSAL_FACTOR = 1.0

# This quantity prevents points which have all been observed at the same quantity from yielding a covariance
# with zero length scale. This could happen if, for example, all the lower points are associated with a single
# integer value.
STD_EPSILON_HACK = 1.0e-8


# TODO(RTL-119): Need to decide about success_progress being used here instead of total_progress
#              Complicated perhaps because it is not strictly increasing
def get_experiment_phase(budget, observation_count, failure_count):
  success_progress = (observation_count - failure_count) / budget
  total_progress = observation_count / budget
  success_proportion = 1 - failure_count / (1 + observation_count)
  if success_progress < INITIALIZATION_PHASE_LIMIT and not (
    total_progress > 2 * INITIALIZATION_PHASE_LIMIT and success_proportion > MINIMUM_SUCCESS_THRESHOLD
  ):
    phase = INITIALIZATION_PHASE
  elif success_progress < SKO_PHASE_LIMIT:
    phase = SKO_PHASE
  else:
    phase = COMPLETION_PHASE
  return phase, success_progress


def get_solver_options(phase, progress):
  if phase == SKO_PHASE:
    progress_step = (progress - INITIALIZATION_PHASE_LIMIT) / (SKO_PHASE_LIMIT - INITIALIZATION_PHASE_LIMIT)
    gamma = TOP_GAMMA - progress_step * (TOP_GAMMA - BOTTOM_GAMMA)
    proposal_factor = SPE_PROPOSAL_FACTOR
  else:
    gamma = BOTTOM_GAMMA
    proposal_factor = numpy.random.uniform(0.0, 0.5)
  return gamma, proposal_factor


class SPENextPoints(View):
  view_name = "spe_next_points"

  # TODO(RTL-83): Fix this
  def remove_task_info_as_needed(self, x):
    if not self.task_options.size or not x.size:
      return x
    return x[:, :-1]

  @staticmethod
  def form_one_hot_covariance(covariance_class, domain, one_hot_points, cat_length_scale, factor):
    point_spread = numpy.std(one_hot_points, axis=0) + STD_EPSILON_HACK
    one_hot_bandwidths = factor * numpy.sqrt(point_spread / 2)

    hyperparameters = [1.0]
    numerical_ind = [
      m["input_ind"]
      for m in domain.one_hot_to_categorical_mapping
      if m["var_type"] != CATEGORICAL_EXPERIMENT_PARAMETER_NAME
    ]
    for one_hot_ind, bandwidth in enumerate(one_hot_bandwidths):
      if one_hot_ind in numerical_ind:
        hyperparameters.append(bandwidth**2)
      else:
        hyperparameters.append(cat_length_scale)
    safe_hyperparameters = [1.0 for x in hyperparameters]
    try:
      covariance = covariance_class(hyperparameters)
    except HyperparameterInvalidError:
      covariance = covariance_class(safe_hyperparameters)

    return covariance

  def form_sigopt_parzen_estimator(
    self,
    one_hot_points_sampled_points,
    points_sampled_values,
    gamma=TOP_GAMMA,
  ):
    temp_covariance = C4RadialMatern([1.0] * (1 + self.domain.one_hot_dim))
    sigopt_parzen_estimator = SigOptParzenEstimator(
      lower_covariance=temp_covariance,
      greater_covariance=temp_covariance,
      points_sampled_points=one_hot_points_sampled_points,
      points_sampled_values=points_sampled_values,
      gamma=gamma,
      forget_factor=MAX_FORGET_FACTOR,
    )
    lower_covariance = self.form_one_hot_covariance(
      covariance_class=C4RadialMatern,
      domain=self.domain,
      one_hot_points=sigopt_parzen_estimator.lower_points,
      cat_length_scale=SPE_CAT_LENGTH_SCALE,
      factor=1.0,
    )
    greater_covariance = self.form_one_hot_covariance(
      covariance_class=C4RadialMatern,
      domain=self.domain,
      one_hot_points=sigopt_parzen_estimator.greater_points,
      cat_length_scale=SPE_CAT_LENGTH_SCALE,
      factor=10.0,
    )
    sigopt_parzen_estimator.update_covariances(lower_covariance, greater_covariance)
    return sigopt_parzen_estimator

  @staticmethod
  def suggest_next_points_constant_liar(sigopt_parzen_estimator, num_to_sample, domain, num_multistarts):
    lie_data = sigopt_parzen_estimator.stash_lies()

    if domain.is_constrained:
      base_optimizer = SLSQPOptimizer(domain.one_hot_domain, sigopt_parzen_estimator)
    else:
      base_optimizer = LBFGSBOptimizer(domain.one_hot_domain, sigopt_parzen_estimator)
    multistart_optimizer = MultistartOptimizer(base_optimizer, num_multistarts=num_multistarts)
    suggestion_list = []
    for _ in range(num_to_sample):
      num_lower_points = len(sigopt_parzen_estimator.lower_points)
      sorted_index_by_eis = sigopt_parzen_estimator.evaluate_expected_improvement(
        sigopt_parzen_estimator.lower_points)[2].argsort()[::-1]
      inbound = numpy.array(
        [
          domain.check_point_acceptable(point)
          for point in domain.map_one_hot_points_to_categorical(sigopt_parzen_estimator.lower_points)
        ]
      )
      selected_starts_indexes = sorted_index_by_eis[: min(5, num_lower_points)]
      selected_starts = sigopt_parzen_estimator.lower_points[selected_starts_indexes, :]
      # NOTE: If none of the selected start is inside the bounded domain, we replace one of the starting points
      # with one of the lower_points that is inbound
      if not any(inbound[selected_starts_indexes]):
        selected_starts[-1, :] = sigopt_parzen_estimator.lower_points[
          numpy.argmax(inbound[sorted_index_by_eis] == 1), :
        ]  # Since True is represented as 1 in python
      new_suggestion, _ = multistart_optimizer.optimize(selected_starts=selected_starts)
      suggestion_list.append(new_suggestion)
      sigopt_parzen_estimator.append_lies([new_suggestion])

    sigopt_parzen_estimator.recover_lies(lie_data)
    # The solver can return points such as -2e-16, which, during the one hot snapping, yields problems
    # This restriction prevents such issues, although perhaps this should be occurring in the solver
    return domain.one_hot_domain.restrict_points_to_domain(numpy.array(suggestion_list))

  # NOTE: I'm worried about sampling effectively in problems with categories
  #       May want to change the uniform random sampling to account for those situations
  @staticmethod
  def draw_samples(
    sigopt_parzen_estimator,
    num_to_sample,
    domain,
    num_multistarts=SPE_NUM_MULTISTARTS,
    batch_size=SPE_BATCH_SIZE,
    rejection_samples_limit=SPE_REJECTION_SAMPLES_LIMIT,
    proposal_factor=SPE_PROPOSAL_FACTOR,
    proposal_std=0.06,
  ):
    max_location = SPENextPoints.suggest_next_points_constant_liar(
      sigopt_parzen_estimator,
      1,
      domain,
      num_multistarts,
    )[0]
    max_value = sigopt_parzen_estimator.evaluate_expected_improvement(numpy.atleast_2d(max_location))[2][0]

    uniform_domain = deepcopy(domain.one_hot_domain)
    uniform_domain.set_quasi_random_sampler_opts(sampler="uniform")

    num_rejection_samples = 0
    samples = numpy.empty((0, domain.one_hot_dim))
    # NOTE: lower_points are sorted by objective function values in decreasing order
    num_lower_points_used = max(1, int(proposal_factor * len(sigopt_parzen_estimator.lower_points)))
    while len(samples) < num_to_sample and num_rejection_samples < rejection_samples_limit:
      test_points_list = []
      for lower_point in sigopt_parzen_estimator.lower_points[:num_lower_points_used]:
        pts = uniform_domain.generate_random_points_near_point(
          batch_size // num_lower_points_used + 1,
          lower_point,
          proposal_std,
        )
        test_points_list.append(pts)
      test_points = numpy.concatenate(test_points_list, axis=0)[:batch_size, :]

      test_ei_vals_scaled = sigopt_parzen_estimator.evaluate_expected_improvement(test_points)[2] / max_value
      test_probs = numpy.random.random(batch_size)
      samples = numpy.concatenate((samples, test_points[test_probs < test_ei_vals_scaled, :]), axis=0)
      num_rejection_samples += batch_size

    if len(samples) < num_to_sample:
      remaining_uniform_samples = uniform_domain.generate_quasi_random_points_in_domain(num_to_sample - len(samples))
      samples = numpy.concatenate((samples, remaining_uniform_samples), axis=0)
    elif len(samples) > num_to_sample:
      samples = samples[numpy.random.choice(range(len(samples)), size=num_to_sample, replace=False), :]

    return samples, num_rejection_samples, max_value, num_lower_points_used

  def augment_failures_with_user_specified_thresholds_violations(self):
    observed_failures = self.points_sampled_failures
    if not (
      self.params["metrics_info"].requires_pareto_frontier_optimization or self.has_constraint_metrics
    ):  # Not a multimetric problem
      return observed_failures

    num_points = len(self.points_sampled_failures)
    bounds_violations = numpy.zeros(num_points, dtype=bool)
    if self.params["metrics_info"].requires_pareto_frontier_optimization:
      bounds_violations = identify_scaled_values_exceeding_scaled_upper_thresholds(
        self.points_sampled_for_af_values,
        self.optimized_metrics_thresholds,
      )
    metric_constraints_violations = numpy.zeros(num_points, dtype=bool)
    if self.has_constraint_metrics:
      metric_constraints_violations = identify_scaled_values_exceeding_scaled_upper_thresholds(
        self.points_sampled_for_pf_values,
        self.constraint_thresholds,
      )
    either_failure = observed_failures | bounds_violations | metric_constraints_violations

    if (
      numpy.sum(bounds_violations) > num_points - MULTIMETRIC_MIN_NUM_IN_BOUNDS_POINTS
      or numpy.sum(metric_constraints_violations) > num_points - MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS
      or numpy.sum(either_failure) > num_points - MULTIMETRIC_MIN_NUM_SUCCESSFUL_POINTS
    ):
      return observed_failures

    return either_failure

  def create_random_suggestions(self, num_to_sample):
    if self.domain.priors and not self.domain.constraint_list:
      suggested_points = self.domain.generate_random_points_according_to_priors(num_to_sample)
    else:
      suggested_points = self.domain.generate_quasi_random_points_in_domain(num_to_sample)

    return self._return_results_to_zigopt(suggested_points)

  def create_spe_suggestions(self, num_to_sample, phase, progress):
    # set params from phase
    gamma, proposal_factor = get_solver_options(phase, progress)
    assert 0 < gamma < 1
    assert 0 < proposal_factor <= 1

    # Here, we counting points as failures whether they actually were reported failures or if they exceed
    # the user's bounds.  I think there's another model we could build in this setting but not sure yet.
    failures_or_beyond_bounds = self.augment_failures_with_user_specified_thresholds_violations()
    one_hot_points_sampled_points, points_sampled_values = filter_multimetric_points_sampled_spe(
      self.multimetric_info,
      self.one_hot_points_sampled_points,
      self.points_sampled_for_af_values,
      failures_or_beyond_bounds,
      self.scaled_optimized_lie_values,
    )
    one_hot_points_sampled_points = self.remove_task_info_as_needed(one_hot_points_sampled_points)
    one_hot_points_being_sampled_points = self.remove_task_info_as_needed(self.one_hot_points_being_sampled_points)

    observation_count = len(one_hot_points_sampled_points)
    open_suggestion_count = len(one_hot_points_being_sampled_points)
    sample_randomly = (
      observation_count <= SPE_OPEN_SUGGESTION_RATIO_BOUND * open_suggestion_count
    )

    try:
      sigopt_parzen_estimator = self.form_sigopt_parzen_estimator(
        one_hot_points_sampled_points,
        points_sampled_values,
        gamma,
      )
    except SPEInsufficientDataError:
      sigopt_parzen_estimator = None

    if sample_randomly or sigopt_parzen_estimator is None:
      return self.create_random_suggestions(num_to_sample)

    sigopt_parzen_estimator.append_lies(list(one_hot_points_being_sampled_points))
    oh_suggested_points, num_rejection_samples, max_value, num_proposal_points = self.draw_samples(
      sigopt_parzen_estimator,
      num_to_sample,
      self.domain,
      proposal_factor=proposal_factor,
    )
    suggested_points = self.domain.map_one_hot_points_to_categorical(oh_suggested_points)
    self.tag.update({"num_rejection_samples": num_rejection_samples})
    self.tag.update({"num_proposal_points": num_proposal_points})
    self.tag.update({"max_ei": max_value})

    return self._return_results_to_zigopt(suggested_points)

  def _return_results_to_zigopt(self, suggested_points):
    results = {
      "endpoint": self.view_name,
      "points_to_sample": suggested_points,
      "tag": self.tag,
    }
    if self.task_options.size:
      results["task_costs"] = select_random_task_by_softmax(self.task_options, size=len(suggested_points)).tolist()
    return results

  def view(self):
    assert self.has_optimization_metrics, f"{self.view_name} must have optimization metrics"
    num_to_sample = self.params["num_to_sample"]

    budget = self.params["metrics_info"].observation_budget or self.domain.dim * SPE_PHANTOM_BUDGET_FACTOR
    phase, progress = get_experiment_phase(
      budget=budget,
      observation_count=len(self.params["points_sampled"].points),
      failure_count=numpy.sum(self.params["points_sampled"].failures),
    )
    self.tag.update({"spe_phase": phase})

    if phase == INITIALIZATION_PHASE:
      return self.create_random_suggestions(num_to_sample)

    return self.create_spe_suggestions(num_to_sample, phase, progress)
