# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from zigopt.common import *
from zigopt.db.util import DeleteClause
from zigopt.observation.model import Observation
from zigopt.services.base import Service
from zigopt.suggestion.lib import SuggestionAlreadyProcessedError
from zigopt.suggestion.model import Suggestion
from zigopt.suggestion.processed.model import ProcessedSuggestion
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class ProcessedSuggestionService(Service):
  """
    Fetches suggestions to be shown to user
    """

  def find_by_experiment(self, experiment, include_deleted=False):
    return self.services.database_service.all(
      self.query_by_experiment(experiment.id, include_deleted).order_by(desc(ProcessedSuggestion.processed_time))
    )

  def query_open_by_experiment(self, experiment_id, include_deleted):
    """
        'open' suggestions have not yet been reported by an observation
        """
    return (
      self.query_by_experiment(experiment_id, include_deleted).outerjoin(Observation).filter(Observation.id.is_(None))
    )

  def query_by_experiment(self, experiment_id, include_deleted):
    return self._include_deleted_clause(
      include_deleted,
      self.services.database_service.query(ProcessedSuggestion).filter(
        ProcessedSuggestion.experiment_id == experiment_id
      ),
    )

  def find_open_by_experiment(self, experiment_id, include_deleted=False):
    return self.services.database_service.all(
      self.query_open_by_experiment(experiment_id, include_deleted).order_by(desc(ProcessedSuggestion.processed_time))
    )

  def find_matching_suggestion(self, experiment, suggestion):
    assignments = suggestion.get_assignments(experiment)
    return self.services.database_service.first(
      self.query_by_experiment(experiment.id, include_deleted=False)
      .join(UnprocessedSuggestion, ProcessedSuggestion.suggestion_id == UnprocessedSuggestion.id)
      .filter(UnprocessedSuggestion.suggestion_meta.suggestion_data.assignments_map == assignments)
      .filter(UnprocessedSuggestion.id != suggestion.id)
    )

  def find_matching_open_suggestion(self, experiment, suggestion):
    assignments = suggestion.get_assignments(experiment)
    return self.services.database_service.first(
      self.query_open_by_experiment(experiment.id, include_deleted=False)
      .join(UnprocessedSuggestion, ProcessedSuggestion.suggestion_id == UnprocessedSuggestion.id)
      .filter(UnprocessedSuggestion.suggestion_meta.suggestion_data.assignments_map == assignments)
      .filter(UnprocessedSuggestion.id != suggestion.id)
    )

  def replace_unprocessed(self, experiment, processed_suggestion, replacement_unprocessed):
    self.services.unprocessed_suggestion_service.insert_suggestions_to_be_processed([replacement_unprocessed])
    assert self.services.database_service.update_one(
      self.services.database_service.query(ProcessedSuggestion).filter(
        ProcessedSuggestion.suggestion_id == processed_suggestion.suggestion_id
      ),
      {ProcessedSuggestion.suggestion_id: replacement_unprocessed.id},
    )
    processed_suggestion.suggestion_id = replacement_unprocessed.id
    return Suggestion(
      processed=processed_suggestion,
      unprocessed=replacement_unprocessed,
    )

  def count_by_experiment(self, experiment_id, include_deleted=DeleteClause.NOT_DELETED):
    return self.services.database_service.count(self.query_by_experiment(experiment_id, include_deleted))

  def count_open_by_experiment(self, experiment_id, include_deleted=DeleteClause.NOT_DELETED):
    return self.services.database_service.count(self.query_open_by_experiment(experiment_id, include_deleted))

  def find_by_id(self, suggestion_id, include_deleted=False):
    return list_get(self.find_by_ids([suggestion_id], include_deleted), 0)

  def find_by_ids(self, suggestion_ids, include_deleted=False):
    if suggestion_ids:
      return self.services.database_service.all(
        self._include_deleted_clause(
          include_deleted,
          self.services.database_service.query(ProcessedSuggestion).filter(
            ProcessedSuggestion.suggestion_id.in_(suggestion_ids)
          ),
        )
      )
    else:
      return []

  def insert(self, processed_suggestion):
    try:
      return self.insert_all([processed_suggestion])
    except IntegrityError as e:
      raise SuggestionAlreadyProcessedError(processed_suggestion) from e

  def insert_all(self, processed_suggestions):
    if processed_suggestions:
      try:
        self.services.database_service.insert_all(processed_suggestions)
      except IntegrityError:
        self.services.database_service.rollback_session()
        raise
    return True

  def delete_all_for_experiment(self, experiment):
    """
        Not a true DB delete, just sets the deleted flag.
        """
    self.services.database_service.update(
      self.services.database_service.query(ProcessedSuggestion).filter(
        ProcessedSuggestion.experiment_id == experiment.id
      ),
      {ProcessedSuggestion.deleted: True},
    )

  def set_delete_by_ids(self, experiment, suggestion_ids, deleted=True):
    if suggestion_ids:
      self.services.database_service.update(
        self.services.database_service.query(ProcessedSuggestion)
        .filter(ProcessedSuggestion.experiment_id == experiment.id)
        .filter(ProcessedSuggestion.suggestion_id.in_(suggestion_ids)),
        {ProcessedSuggestion.deleted: deleted},
      )

  def delete_open_for_experiment(self, experiment):
    open_suggestions = self.find_open_by_experiment(experiment.id)
    self.set_delete_by_ids(experiment, [s.suggestion_id for s in open_suggestions])

  def _include_deleted_clause(self, include_deleted, q):
    if isinstance(include_deleted, DeleteClause):
      if include_deleted == DeleteClause.ALL:
        return q
      elif include_deleted == DeleteClause.DELETED:
        return q.filter(ProcessedSuggestion.deleted.is_(True))
      else:
        assert include_deleted == DeleteClause.NOT_DELETED
        return q.filter(ProcessedSuggestion.deleted.isnot(True))
    else:
      assert is_boolean(include_deleted)
      if include_deleted:
        return q
      return q.filter(ProcessedSuggestion.deleted.isnot(True))

  def upsert_suggestion(self, suggestion):
    self.services.database_service.upsert(suggestion)
