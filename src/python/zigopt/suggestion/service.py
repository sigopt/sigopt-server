# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.db.util import DeleteClause
from zigopt.services.base import Service
from zigopt.suggestion.model import Suggestion
from zigopt.suggestion.processed.model import ProcessedSuggestion
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class SuggestionService(Service):
  """
    Fetches suggestions from the DB. Doesn't take care of processing suggestions.
    """

  def find_by_id(self, suggestion_id, deleted=DeleteClause.NOT_DELETED):
    """
        suggestion_id is the id of a processed suggestion
        """
    return list_get(self.find_by_ids([suggestion_id], deleted), 0)

  def find_by_ids(self, suggestion_ids, deleted=DeleteClause.NOT_DELETED):
    """
        suggestion_id is the id of a processed suggestion
        """
    if not suggestion_ids:
      return []

    objects = self.services.database_service.all(
      self._include_deleted_clause(
        deleted,
        self.services.database_service.query(ProcessedSuggestion)
        .filter(ProcessedSuggestion.suggestion_id.in_(suggestion_ids))
        .join(UnprocessedSuggestion, ProcessedSuggestion.suggestion_id == UnprocessedSuggestion.id)
        .with_entities(ProcessedSuggestion, UnprocessedSuggestion),
      )
    )

    return self.get_suggestions_set_observations(objects)

  def find_by_experiment(self, experiment, deleted=DeleteClause.NOT_DELETED):
    # Returns all processed suggestions for a given experiment.
    objects = self.services.database_service.all(
      self._include_deleted_clause(
        deleted,
        self.services.database_service.query(ProcessedSuggestion)
        .filter(ProcessedSuggestion.experiment_id == experiment.id)
        .join(UnprocessedSuggestion, ProcessedSuggestion.suggestion_id == UnprocessedSuggestion.id)
        .with_entities(ProcessedSuggestion, UnprocessedSuggestion),
      )
    )

    return self.get_suggestions_set_observations(objects)

  # TODO(SN-1125): Rewrite this to be a join. Currently modified to throw a soft exception, so that
  # we can diagnose if this was ever doing the wrong thing
  @generator_to_list
  def find_open_by_experiment(self, experiment, deleted=False):
    processed_suggestions = self.services.processed_suggestion_service.find_open_by_experiment(
      experiment.id,
      include_deleted=deleted,
    )

    unprocessed_suggestions = self.services.unprocessed_suggestion_service.find_by_ids(
      [p.suggestion_id for p in processed_suggestions],
    )
    unprocessed_suggestions_by_id = to_map_by_key(unprocessed_suggestions, lambda u: u.id)

    for p in processed_suggestions:
      u = unprocessed_suggestions_by_id.get(p.suggestion_id)
      if u:
        yield Suggestion(processed=p, unprocessed=u)
      else:
        self.services.exception_logger.soft_exception(
          f"Processed suggestion {p.suggestion_id} has no corresponding unprocessed suggestion",
          extra=dict(
            suggestion_id=p.suggestion_id,
            experiment_id=experiment.id,
            include_deleted=deleted,
          ),
        )

  def _include_deleted_clause(self, deleted, q):
    if deleted is DeleteClause.NOT_DELETED:
      return q.filter(ProcessedSuggestion.deleted.isnot(True))
    if deleted is DeleteClause.DELETED:
      return q.filter(ProcessedSuggestion.deleted.is_(True))
    assert deleted is DeleteClause.ALL
    return q

  def get_suggestions_set_observations(self, objects):
    suggestions = [
      Suggestion(
        processed=processed,
        unprocessed=unprocessed,
      )
      for (processed, unprocessed) in objects
    ]

    observations_map = dict(
      (o.processed_suggestion_id, o)
      for o in self.services.observation_service.find_by_processed_suggestion_ids(
        [s.id for s in suggestions],
        include_deleted=True,
      )
    )

    for suggestion in suggestions:
      suggestion.set_observation(observations_map.get(suggestion.id))

    return suggestions

  def count_by_experiment(self, experiment, deleted=DeleteClause.NOT_DELETED):
    return self.services.processed_suggestion_service.count_by_experiment(
      experiment.id,
      include_deleted=deleted,
    )

  def count_open_by_experiment(self, experiment, deleted=DeleteClause.NOT_DELETED):
    return self.services.processed_suggestion_service.count_open_by_experiment(
      experiment.id,
      include_deleted=deleted,
    )
