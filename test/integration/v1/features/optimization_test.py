# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from flaky import flaky

from zigopt.common.lists import *
from zigopt.experiment.model import Experiment
from zigopt.observation.model import Observation
from zigopt.optimization_aux.model import ExperimentOptimizationAux
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData, ObservationValue
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData, SuggestionMeta
from zigopt.sigoptcompute.constant import MINIMUM_SUCCESSES_TO_COMPUTE_EI
from zigopt.suggestion.sampler.lhc import LatinHypercubeSampler
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.utils.constants import EXPECTED_GP_OPTIMIZATION_SOURCE
from integration.utils.random_assignment import random_assignments
from integration.utils.wait import wait_for
from integration.v1.test_base import V1Base
from sigoptaux.constant import DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS


@pytest.mark.slow
class TestOptimization(V1Base):
  def skip_over_latin_hypercube_suggestions(
    self,
    services,
    experiment,
    connection,
    db_connection,
  ):
    db_experiment = services.experiment_service.find_by_id(experiment.id)
    sampler = LatinHypercubeSampler(
      services,
      experiment=db_experiment,
      optimization_args=services.optimizer.fetch_optimization_args(db_experiment),
    )
    unprocessed_suggestions = sampler.fetch_best_suggestions(limit=sampler.stencil_length)
    observations = [
      Observation(
        experiment_id=experiment.id,
        data=ObservationData(
          assignments_map=unprocessed.suggestion_meta.suggestion_data.get_assignments(db_experiment),
          values=[ObservationValue(value=0.3 * k)],
        ),
      )
      for k, unprocessed in enumerate(unprocessed_suggestions)
    ]
    services.database_service.insert_all(observations)
    services.optimize_queue_service.enqueue_optimization(
      db_experiment,
      num_observations=len(observations),
    )

    def get_optimized_suggestion():
      suggestion = connection.experiments(experiment.id).suggestions().create()
      # actually processed suggestion, but we need source
      current_suggestion = services.unprocessed_suggestion_service.find_by_id(suggestion.id)
      if current_suggestion.source == EXPECTED_GP_OPTIMIZATION_SOURCE:
        return current_suggestion
      connection.experiments(experiment.id).suggestions(suggestion.id).delete()
      return None

    return wait_for(get_optimized_suggestion)

  # NOTE: The reason this test is flaky is because QEI has randomness
  @flaky(max_runs=3)
  def test_best_suggestions_are_returned(
    self,
    services,
    connection,
    db_connection,
  ):
    parameters = [  # It makes it easier to deal with the SuggestionMeta if there are no categoricals
      {"name": "x0", "type": "double", "bounds": {"min": -1, "max": 1}},
      {"name": "x1", "type": "double", "bounds": {"min": -1, "max": 1}},
      {"name": "x2", "type": "int", "bounds": {"min": -14, "max": 12}},
    ]
    with connection.create_experiment({"parameters": parameters}) as experiment:
      current_suggestion = self.skip_over_latin_hypercube_suggestions(
        services,
        experiment,
        connection,
        db_connection,
      )
      db_experiment = self.get_db_experiment(db_connection, experiment)
      suggestions_before = services.unprocessed_suggestion_service.get_suggestions_per_source(db_experiment)
      connection.experiments(experiment.id).observations().create(
        suggestion=current_suggestion.id,
        values=[{"value": 2.6}],
        no_optimize=False,
      )

      def get_new_suggestions():
        available_suggestions = services.unprocessed_suggestion_service.get_suggestions_per_source(db_experiment)
        new_suggestions = [
          s for s in available_suggestions if s.uuid_value not in [s2.uuid_value for s2 in suggestions_before]
        ]
        return new_suggestions

      new_suggestions_created = wait_for(get_new_suggestions)
      available_suggestions = services.unprocessed_suggestion_service.get_suggestions_per_source(db_experiment)

      for _ in new_suggestions_created:
        # Need to grab the args before a new open suggestion is created
        optimization_args = services.optimizer.fetch_optimization_args(db_experiment)
        s = connection.experiments(experiment.id).suggestions().create()
        s_id = int(s.id)
        db_suggestion = db_connection.one(
          db_connection.query(UnprocessedSuggestion).filter(UnprocessedSuggestion.id == s.id)
        )
        s_uuid = db_suggestion.uuid_value

        # If the suggestion was from the padding, make sure to include it in the ranking we do now
        random_padding_suggestions = []
        if s_uuid not in [t.uuid_value for t in available_suggestions]:
          suggestion_meta = SuggestionMeta(suggestion_data=SuggestionData(assignments_map=s.assignments))
          newest_suggestion = UnprocessedSuggestion(id=s_id, uuid_value=s_uuid, suggestion_meta=suggestion_meta)
          random_padding_suggestions.append(newest_suggestion)

        highest_ranked = services.suggestion_ranker.get_ranked_suggestions_excluding_low_score(
          available_suggestions,
          optimization_args,
          random_padding_suggestions,
        )[0]
        assert highest_ranked.uuid_value == s_uuid
        available_suggestions.pop(find_index(available_suggestions, lambda x: x.uuid_value == s_uuid))

  def test_first_suggestion(
    self,
    services,
    connection,
    db_connection,
    wait_for_empty_optimization_queue,
  ):
    with connection.create_any_experiment() as experiment:
      db_experiment = self.get_db_experiment(db_connection, experiment)
      assert db_experiment
      assert self.get_hyperparameters(db_connection, experiment, wait_for_empty_optimization_queue) is None
      assert services.unprocessed_suggestion_service.get_suggestions_per_source(experiment) == []
      assert services.processed_suggestion_service.find_by_experiment(experiment) == []

      s = connection.experiments(experiment.id).suggestions().create()
      assert self.get_hyperparameters(db_connection, experiment, wait_for_empty_optimization_queue) is None
      # actually processed suggestion, but we need source
      unprocessed_suggestions = services.unprocessed_suggestion_service.find_by_experiment(experiment)
      assert len(unprocessed_suggestions) == 1
      initial_suggestion = unprocessed_suggestions[0]
      if any(p.prior is not None for p in experiment.parameters):
        assert initial_suggestion.source == UnprocessedSuggestion.Source.LOW_DISCREPANCY_RANDOM
      else:
        assert initial_suggestion.source == UnprocessedSuggestion.Source.LATIN_HYPERCUBE

      connection.experiments(experiment.id).observations().create(
        suggestion=s.id,
        values=[{"value": 2.6}],
        no_optimize=False,
      )
      # NOTE: the optimization messages for the previous call sometimes take longer than 10s to process
      wait_for(
        lambda: self.get_hyperparameters(db_connection, experiment, wait_for_empty_optimization_queue) is not None,
        timeout=20,
      )

      redis_unprocessed_suggestions = services.unprocessed_suggestion_service.get_suggestions_per_source(db_experiment)
      redis_generated_suggestions = [
        s for s in redis_unprocessed_suggestions if s.uuid_value != initial_suggestion.uuid_value
      ]
      assert not redis_generated_suggestions

      for k in range(MINIMUM_SUCCESSES_TO_COMPUTE_EI):
        s = connection.experiments(experiment.id).suggestions().create()
        connection.experiments(experiment.id).observations().create(
          suggestion=s.id,
          values=[{"value": 2.6 + k}],
          no_optimize=False,
        )

      def get_redis_suggestions():
        redis_unprocessed_suggestions = services.unprocessed_suggestion_service.get_suggestions_per_source(
          db_experiment
        )
        redis_generated_suggestions = [
          s for s in redis_unprocessed_suggestions if s.uuid_value != initial_suggestion.uuid_value
        ]
        return redis_generated_suggestions

      redis_generated_suggestions = wait_for(get_redis_suggestions)
      assert all(s.source == EXPECTED_GP_OPTIMIZATION_SOURCE for s in redis_generated_suggestions)

      unprocessed_suggestions = services.unprocessed_suggestion_service.find_by_experiment(experiment)
      generated_suggestions = [s for s in unprocessed_suggestions if s.id != initial_suggestion.id]
      assert generated_suggestions
      assert not all(s.source == EXPECTED_GP_OPTIMIZATION_SOURCE for s in generated_suggestions)
      assert all(
        s.source in (EXPECTED_GP_OPTIMIZATION_SOURCE, initial_suggestion.source) for s in generated_suggestions
      )

  @pytest.mark.parametrize("experiment_type", ["random", "grid"])
  def test_no_optimize_experiments(
    self,
    services,
    connection,
    db_connection,
    experiment_type,
    wait_for_empty_optimization_queue,
  ):
    with connection.create_any_experiment(type=experiment_type) as experiment:
      s = connection.experiments(experiment.id).suggestions().create()
      connection.experiments(experiment.id).observations().create(
        suggestion=s.id,
        values=[{"value": 2.6}],
        no_optimize=False,
      )
      assert self.get_hyperparameters(db_connection, experiment, wait_for_empty_optimization_queue) is None

  def get_db_experiment(self, db_connection, experiment):
    return db_connection.first(db_connection.query(Experiment).filter_by(id=experiment.id))

  def get_hyperparameters(self, db_connection, experiment, wait_for_empty_optimization_queue, timeout=10):
    wait_for_empty_optimization_queue(timeout=timeout)
    return db_connection.first(db_connection.query(ExperimentOptimizationAux).filter_by(experiment_id=experiment.id))

  def test_spe(self, services, connection, db_connection):
    dimension = DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS + 1
    # Set the budget large enough to get past the necessary LDS phase (defined by the stencil)
    # This is a byproduct of the fact that the LDS sampler supersedes the RankedSampler early in the budget
    budget = 3 * dimension

    params = [{"name": str(i), "type": "double", "bounds": {"min": 10, "max": 20}} for i in range(dimension - 1)] + [
      {"name": "categorical", "type": "categorical", "categorical_values": [{"name": "a"}, {"name": "b"}]},
    ]
    with connection.create_experiment({"name": "use spe", "parameters": params, "observation_budget": budget}) as e:
      suggestions = []
      # Note - Not sure what this is doing here, except maybe testing parallelism??
      for _ in range(5):
        suggestions.append(connection.experiments(e.id).suggestions().create())
      for s in suggestions:
        connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 10}], no_optimize=False)

      # Confirm that the suggestions being created are actually SPE suggestions (not excluded through any EI check)
      observations = [
        {"assignments": random_assignments(e), "values": [{"value": k / 25.0}]} for k in range(budget - 1)
      ]
      self.batch_upload_observations(e, observations, no_optimize=False)

      suggestion = connection.experiments(e.id).suggestions().create()
      # actually processed suggestion, but we need source
      unprocessed_suggestion = services.unprocessed_suggestion_service.find_by_id(suggestion.id)
      assert unprocessed_suggestion.source == UnprocessedSuggestion.Source.SPE
