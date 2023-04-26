# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.assignments.build import set_assignments_map_from_proxy
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData, SuggestionMeta
from zigopt.protobuf.lib import copy_protobuf
from zigopt.queued_suggestion.model import QueuedSuggestion
from zigopt.services.base import Service
from zigopt.suggestion.processed.model import ProcessedSuggestion
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class QueuedSuggestionService(Service):
  def insert(self, queued):
    return self.services.database_service.insert(queued)

  def find_next(self, experiment_id, include_deleted=False):
    claimed_ids = flatten(
      self.services.database_service.all(
        self.services.database_service.query(ProcessedSuggestion.queued_id)
        .filter_by(experiment_id=experiment_id)
        .filter(ProcessedSuggestion.queued_id.isnot(None))
      )
    )

    q = self.query_by_experiment_id(experiment_id, include_deleted=include_deleted)
    if claimed_ids:
      q = q.filter(~(QueuedSuggestion.id.in_(claimed_ids)))
    q = q.order_by(QueuedSuggestion.id)
    return self.services.database_service.first(q)

  def find_by_id(self, experiment_id, queued_id, include_deleted=False):
    q = self.services.database_service.query(QueuedSuggestion).filter_by(experiment_id=experiment_id, id=queued_id)
    q = self._include_deleted_clause(include_deleted, q)
    return self.services.database_service.one_or_none(q)

  def delete_by_id(self, experiment_id, queued_id):
    suggestion = self.find_by_id(experiment_id, queued_id)
    if suggestion:
      meta = copy_protobuf(suggestion.meta)
      meta.deleted = True
      self.services.database_service.update_one(
        self.services.database_service.query(QueuedSuggestion).filter_by(experiment_id=experiment_id, id=queued_id),
        {QueuedSuggestion.meta: meta},
      )

  def create_unprocessed_suggestion(self, experiment, queued_suggestion):
    if experiment.id != queued_suggestion.experiment_id:
      raise Exception(
        f"Experiment {experiment.id}"
        f" attempting to processed queue suggestion for experiment {queued_suggestion.experiment_id}"
      )

    suggestion_data = SuggestionData()
    set_assignments_map_from_proxy(suggestion_data, queued_suggestion, experiment)
    if experiment.is_multitask:
      suggestion_data.task.CopyFrom(queued_suggestion.task)
    unprocessed_suggestion = UnprocessedSuggestion(
      experiment_id=experiment.id,
      source=UnprocessedSuggestion.Source.QUEUED_SUGGESTION,
      suggestion_meta=SuggestionMeta(suggestion_data=suggestion_data),
    )
    self.services.database_service.insert(unprocessed_suggestion)
    return unprocessed_suggestion

  def query_by_experiment_id(self, experiment_id, include_deleted=False):
    return self._include_deleted_clause(
      include_deleted,
      self.services.database_service.query(QueuedSuggestion).filter_by(experiment_id=experiment_id),
    )

  def _include_deleted_clause(self, include_deleted, q):
    if not include_deleted:
      return q.filter(~QueuedSuggestion.meta.deleted.as_boolean())
    return q
