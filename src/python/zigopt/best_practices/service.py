# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.best_practices.constants import *
from zigopt.experiment.progress import ExperimentObservationProgress
from zigopt.services.base import Service


class BestPracticesService(Service):
  @generator_to_safe_iterator
  def check_experiment(self, experiment):
    num_observations = self.services.observation_service.count_by_experiment(experiment)
    num_open_suggestions = self.services.suggestion_service.count_open_by_experiment(experiment)
    progress = self.services.experiment_progress_service.progress_for_experiments([experiment]).get(experiment.id)

    yield from self.check_max_observations(experiment, num_observations)
    if isinstance(progress, ExperimentObservationProgress):
      observation_budget_consumed = progress.observation_budget_consumed
      yield from self.check_observation_budget_consumed(experiment, observation_budget_consumed)
    yield from self.check_max_open_suggestions(experiment, num_open_suggestions)
    yield from self.check_parallel_bandwidth(experiment)
    yield from self.check_conditionals_breadth(experiment)
    yield from self.check_max_constraints(experiment)
    yield from self.check_observation_budget(experiment)
    yield from self.check_max_dimension(experiment)

  @generator_to_safe_iterator
  def check_max_observations(self, experiment, num_observations):
    if experiment.constraints and not num_observations <= MAX_OBSERVATIONS_WITH_CONSTRAINTS:
      yield f"{CONSTRAINTS_REASON} has more than {MAX_OBSERVATIONS_WITH_CONSTRAINTS} observations"

    if experiment.conditionals and not num_observations <= MAX_OBSERVATIONS_WITH_CONDITIONALS:
      yield f"{CONDITIONALS_REASON} has more than {MAX_OBSERVATIONS_WITH_CONDITIONALS} observations"

  @generator_to_safe_iterator
  def check_observation_budget_consumed(self, experiment, observation_budget_consumed):
    if experiment.observation_budget and observation_budget_consumed > experiment.observation_budget:
      rounded_budget_consumed = (
        int(observation_budget_consumed)
        if is_integer_valued_number(observation_budget_consumed)
        else round(observation_budget_consumed, 3)
      )
      yield (
        f"Observation budget consumed {rounded_budget_consumed}"
        f" exceeds the observation_budget {experiment.observation_budget}"
      )

  @generator_to_safe_iterator
  def check_max_open_suggestions(self, experiment, num_open_suggestions):
    if experiment.parallel_bandwidth:
      if not num_open_suggestions <= experiment.parallel_bandwidth:
        yield (
          f"number of open suggestions ({num_open_suggestions})"
          f" exceeds parallel_bandwidth ({experiment.parallel_bandwidth})"
        )

    if not num_open_suggestions <= experiment.dimension:
      if experiment.constraints:
        yield (
          f"{CONSTRAINTS_REASON} has more open suggestions ({num_open_suggestions})"
          f" than parameters ({experiment.dimension})"
        )

      if experiment.conditionals:
        yield (
          f"{CONDITIONALS_REASON} has more open suggestions ({num_open_suggestions})"
          f" than parameters ({experiment.dimension})"
        )

  @generator_to_safe_iterator
  def check_parallel_bandwidth(self, experiment):
    if experiment.parallel_bandwidth:
      if not experiment.parallel_bandwidth <= experiment.dimension:
        if experiment.constraints:
          yield (
            f"{CONSTRAINTS_REASON} has a larger parallel_bandwidth ({experiment.parallel_bandwidth})"
            f" than number of parameters ({experiment.dimension})"
          )

        if experiment.conditionals:
          yield (
            f"{CONDITIONALS_REASON} has a larger parallel_bandwidth ({experiment.parallel_bandwidth})"
            f" than number of parameters ({experiment.dimension})"
          )

  @generator_to_safe_iterator
  def check_max_constraints(self, experiment):
    if experiment.constraints and not len(experiment.constraints) <= MAX_LINEAR_CONSTRAINTS:
      yield f"{CONSTRAINTS_REASON} has more than {MAX_LINEAR_CONSTRAINTS} constraints"

  @generator_to_safe_iterator
  def check_conditionals_breadth(self, experiment):
    if experiment.conditionals and not experiment.conditionals_breadth <= MAX_CONDITIONALS_BREADTH:
      yield f"{CONDITIONALS_REASON} has more than {MAX_CONDITIONALS_BREADTH} conditionals"

  @generator_to_safe_iterator
  def check_observation_budget(self, experiment):
    if experiment.observation_budget:
      if experiment.constraints and not experiment.observation_budget <= MAX_OBSERVATIONS_WITH_CONSTRAINTS:
        yield f"{CONSTRAINTS_REASON} has observation_budget greater than {MAX_OBSERVATIONS_WITH_CONSTRAINTS}"
      elif experiment.conditionals and not experiment.observation_budget <= MAX_OBSERVATIONS_WITH_CONDITIONALS:
        yield f"{CONDITIONALS_REASON} has observation_budget greater than {MAX_OBSERVATIONS_WITH_CONDITIONALS}"

  @generator_to_safe_iterator
  def check_max_dimension(self, experiment):
    if experiment.constraints and not experiment.dimension <= MAX_DIMENSION_WITH_CONSTRAINTS:
      yield f"{CONSTRAINTS_REASON} has more than {MAX_DIMENSION_WITH_CONSTRAINTS} parameters"

    if experiment.conditionals and not experiment.dimension <= MAX_DIMENSION_WITH_CONDITIONALS:
      yield f"{CONDITIONALS_REASON} has more than {MAX_DIMENSION_WITH_CONDITIONALS} parameters"

  def notify_admins(self, auth, error_message, experiment, **kwargs):
    # Note: error_message can be a message or an array
    if self.services.config_broker.get("features.bestPractices", False):
      if "organization_id" not in kwargs:
        kwargs["organization_id"] = auth and auth.current_client and auth.current_client.organization_id

      if "user_id" not in kwargs:
        kwargs["user_id"] = auth and auth.current_user and auth.current_user.id

      if "client_id" not in kwargs:
        kwargs["client_id"] = auth and auth.current_client and auth.current_client.id

      if "experiment_id" not in kwargs:
        kwargs["experiment_id"] = experiment and experiment.id
