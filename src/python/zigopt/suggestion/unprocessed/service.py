# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import uuid
from datetime import timedelta

from sqlalchemy.exc import IntegrityError

from zigopt.common import *
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.exception.logger import AlreadyLoggedException
from zigopt.profile.timing import time_function
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionMeta
from zigopt.services.base import Service
from zigopt.suggestion.lib import DuplicateUnprocessedSuggestionError
from zigopt.suggestion.model import Suggestion
from zigopt.suggestion.processed.model import ProcessedSuggestion
from zigopt.suggestion.unprocessed.model import (
  SUGGESTIONS_ID_SEQUENCE_NAME,
  SUGGESTIONS_UUID_CONSTRAINT_NAME,
  UnprocessedSuggestion,
)


class UnprocessedSuggestionService(Service):
  def process(
    self,
    experiment,
    unprocessed_suggestion,
    processed_suggestion_meta,
    queued_id=None,
    automatic=False,
  ):
    assert experiment.id == unprocessed_suggestion.experiment_id

    if unprocessed_suggestion.id is None:
      try:
        self.services.unprocessed_suggestion_service.insert_suggestions_to_be_processed([unprocessed_suggestion])
      except DuplicateUnprocessedSuggestionError:
        unprocessed_suggestion = self.services.database_service.one(
          self.services.database_service.query(UnprocessedSuggestion).filter(
            UnprocessedSuggestion.uuid_value == unprocessed_suggestion.uuid_value
          )
        )

    processed_suggestion = ProcessedSuggestion(
      experiment_id=experiment.id,
      processed_suggestion_meta=processed_suggestion_meta,
      queued_id=queued_id,
      suggestion_id=unprocessed_suggestion.id,
      automatic=automatic,
    )

    self.services.processed_suggestion_service.insert(processed_suggestion)
    self.remove_from_available_suggestions(unprocessed_suggestion)

    if processed_suggestion.queued_id:
      self.services.queued_suggestion_service.delete_by_id(
        processed_suggestion.experiment_id,
        processed_suggestion.queued_id,
      )
    return Suggestion(
      processed=processed_suggestion,
      unprocessed=unprocessed_suggestion,
    )

  def delete_all_for_experiment(self, experiment):
    updated_suggestions = []
    for old_suggestion in self.services.database_service.all(
      self.services.database_service.query(UnprocessedSuggestion).filter(
        UnprocessedSuggestion.experiment_id == experiment.id
      )
    ):
      new_suggestion_meta = old_suggestion.suggestion_meta.copy_protobuf()
      new_suggestion_meta.deleted = True
      updated_suggestions.append({"id": old_suggestion.id, "suggestion_meta": new_suggestion_meta})
    self.services.database_service.update_all(UnprocessedSuggestion, updated_suggestions)

  def delete_by_id(self, experiment, suggestion_id):
    suggestion = self.find_by_id(suggestion_id)
    if suggestion:
      new_meta = suggestion.suggestion_meta.copy_protobuf()
      new_meta.deleted = True
      self.services.database_service.update_one(
        self.services.database_service.query(UnprocessedSuggestion)
        .filter(UnprocessedSuggestion.experiment_id == experiment.id)
        .filter(UnprocessedSuggestion.id == suggestion_id),
        {UnprocessedSuggestion.suggestion_meta: new_meta},
      )

  def find_by_ids(self, suggestion_ids, include_deleted=False):
    if suggestion_ids:
      return self.services.database_service.all(
        self._include_deleted_clause(
          include_deleted,
          self.services.database_service.query(UnprocessedSuggestion).filter(
            UnprocessedSuggestion.id.in_(suggestion_ids)
          ),
        )
      )
    else:
      return []

  def find_by_id(self, suggestion_id, include_deleted=False):
    return list_get(self.find_by_ids([suggestion_id], include_deleted), 0)

  def find_by_experiment(self, experiment, include_deleted=False):
    return self.services.database_service.all(
      self._include_deleted_clause(
        include_deleted,
        self.services.database_service.query(UnprocessedSuggestion).filter(
          UnprocessedSuggestion.experiment_id == experiment.id
        ),
      )
    )

  def count_by_experiment(self, experiment, include_deleted=False):
    return self.services.database_service.count(
      self._include_deleted_clause(
        include_deleted,
        self.services.database_service.query(UnprocessedSuggestion).filter_by(experiment_id=experiment.id),
      )
    )

  def insert_suggestions_to_be_processed(self, generated_suggestions):
    generated_suggestions = list(generated_suggestions)
    if generated_suggestions:
      generated_ids = self.services.database_service.reserve_ids(
        SUGGESTIONS_ID_SEQUENCE_NAME,
        len(generated_suggestions),
      )

      for suggestion_id, suggestion in zip(generated_ids, generated_suggestions):
        suggestion.id = suggestion_id

      try:
        self.services.database_service.insert_all(generated_suggestions, return_defaults=False)
      except IntegrityError as e:
        self.services.database_service.rollback_session()
        uuid_msg = f'duplicate key value violates unique constraint "{SUGGESTIONS_UUID_CONSTRAINT_NAME}"'
        if uuid_msg in str(e):
          raise DuplicateUnprocessedSuggestionError("UnprocessedSuggestion already exists") from e
        raise

  def _include_deleted_clause(self, include_deleted, q):
    if not include_deleted:
      return q.filter(~UnprocessedSuggestion.suggestion_meta.deleted.as_boolean())
    return q

  @time_function(
    "sigopt.timing",
    log_attributes=lambda self, experiment, *args, **kwargs: {"experiment": str(experiment.id)},
  )
  def get_suggestions_per_source(self, experiment, sources=None):
    if sources is None:
      sources_key = self.services.redis_key_service.create_sources_key(experiment.id)
      sources = self.services.redis_service.get_set_members(sources_key)

    if len(sources) == 0:
      return []

    unprocessed_suggestions = []
    for source in sources:
      timestamps_by_uuid = {}
      timestamp_key = self.services.redis_key_service.create_suggestion_timestamp_key(experiment.id, source)
      uuid_timestamp_tuples = self.services.redis_service.get_sorted_set_range(timestamp_key, 0, -1, withscores=True)
      timestamps_by_uuid.update(dict(uuid_timestamp_tuples))

      suggestion_protobuf_key = self.services.redis_key_service.create_suggestion_protobuf_key(experiment.id, source)
      suggestions_by_uuid = self.services.redis_service.get_all_hash_fields(suggestion_protobuf_key)

      for suggestion_uuid, suggestion_meta_protobuf in suggestions_by_uuid.items():
        generated_time = timestamps_by_uuid.get(suggestion_uuid, None)
        unprocessed_suggestions.append(
          UnprocessedSuggestion(
            experiment_id=experiment.id,
            generated_time=generated_time,
            source=int(source),
            uuid_value=uuid.UUID(suggestion_uuid.decode("utf-8")),
            suggestion_meta=SuggestionMeta.FromString(suggestion_meta_protobuf),
          )
        )
    return [s for s in unprocessed_suggestions if s.is_valid(experiment)]

  def _truncate_suggestion_length(self, experiment_id, source, num_to_keep):
    stop_index = -num_to_keep - 1  # redis is inclusive of endpoint
    suggestion_timestamp_key = self.services.redis_key_service.create_suggestion_timestamp_key(
      experiment_id,
      source,
    )
    # suggestions are sorted by time created/added; this grabs the oldest ones
    suggestions_to_drop = self.services.redis_service.get_sorted_set_range(suggestion_timestamp_key, 0, stop_index)
    if suggestions_to_drop:
      suggestion_protobuf_key = self.services.redis_key_service.create_suggestion_protobuf_key(experiment_id, source)
      self.services.redis_service.remove_from_hash(suggestion_protobuf_key, *suggestions_to_drop)
      self.services.redis_service.remove_from_sorted_set(suggestion_timestamp_key, *suggestions_to_drop)

  def _store_unprocessed_suggestions(self, experiment_id, unprocessed_suggestions, timestamp=None):
    sources_key = self.services.redis_key_service.create_sources_key(experiment_id)
    suggestions_by_source = as_grouped_dict(unprocessed_suggestions, lambda s: s.source)
    timestamp = timestamp or unix_timestamp(with_microseconds=True)
    expiry = timedelta(days=31)

    for source, suggestions in suggestions_by_source.items():
      self.services.redis_service.add_to_set(sources_key, source)
      self.services.redis_service.set_expire(sources_key, expiry)
      suggestion_protobuf_key = self.services.redis_key_service.create_suggestion_protobuf_key(experiment_id, source)
      suggestion_meta_protobufs_by_uuid = {
        str(suggestion.uuid_value or uuid.uuid4()): suggestion.suggestion_meta.SerializeToString()
        for suggestion in suggestions
      }
      self.services.redis_service.set_hash_fields(suggestion_protobuf_key, suggestion_meta_protobufs_by_uuid)
      self.services.redis_service.set_expire(suggestion_protobuf_key, expiry)

      suggestion_timestamp_key = self.services.redis_key_service.create_suggestion_timestamp_key(
        experiment_id,
        source,
      )
      suggestion_timestamps = [(suggestion_uuid, timestamp) for suggestion_uuid in suggestion_meta_protobufs_by_uuid]
      self.services.redis_service.add_sorted_set_new(suggestion_timestamp_key, suggestion_timestamps)
      self.services.redis_service.set_expire(suggestion_timestamp_key, expiry)

      backlog_multiplier = max(self.services.config_broker.get("model.backlog_multiplier", default=3), 1)
      default_generation_size = self.services.config_broker.get("model.num_suggestions", default=5)
      num_to_keep = max(len(suggestions), default_generation_size) * backlog_multiplier
      self._truncate_suggestion_length(experiment_id, source, num_to_keep)

  @time_function(
    "sigopt.timing",
    lambda self, unprocessed_suggestions, *args, **kwargs: {
      "experiment": (str(unprocessed_suggestions[0].experiment_id) if len(unprocessed_suggestions) else None),
    },
  )
  def insert_unprocessed_suggestions(self, unprocessed_suggestions, timestamp=None):
    if not unprocessed_suggestions:
      return
    suggestions_by_experiment_id = as_grouped_dict(unprocessed_suggestions, lambda s: s.experiment_id)
    if None in suggestions_by_experiment_id:
      raise Exception("Unprocessed suggestions need an experiment_id")
    if len(suggestions_by_experiment_id) > 1:
      self.services.exception_logger.soft_exception(
        "Should only be adding Redis suggestions for one experiment at a time",
        extra={"experiment_ids": list(suggestions_by_experiment_id)},
      )

    for experiment_id, suggestions in suggestions_by_experiment_id.items():
      self._store_unprocessed_suggestions(experiment_id, suggestions, timestamp=timestamp)

  # we may tolerate_timeout when processing is not essential to the success of the call.
  # eg: if we've already made a ProcessedSuggestion, don't let failure here prevent API response
  @time_function(
    "sigopt.timing",
    lambda self, suggestion, *args, **kwargs: {
      "experiment": str(suggestion.experiment_id),
      "suggestion": str(suggestion.id),
    },
  )
  def remove_from_available_suggestions(self, suggestion, tolerate_failure=True):
    experiment_id = suggestion.experiment_id
    source = suggestion.source
    uuid_value = str(suggestion.uuid_value)

    suggestion_protobuf_key = self.services.redis_key_service.create_suggestion_protobuf_key(experiment_id, source)
    suggestion_timestamp_key = self.services.redis_key_service.create_suggestion_timestamp_key(
      experiment_id,
      source,
    )
    try:
      self.services.redis_service.remove_from_hash(suggestion_protobuf_key, uuid_value)
      self.services.redis_service.remove_from_sorted_set(suggestion_timestamp_key, uuid_value)
    except AssertionError:
      raise
    except Exception as e:  # pylint: disable=broad-except
      self.services.exception_logger.soft_exception(
        e,
        extra={
          "function_name": "remove_from_available_suggestions",
          "experiment_id": experiment_id,
          "suggestion_id": suggestion.id,
        },
      )
      if not tolerate_failure:
        raise AlreadyLoggedException(e) from e
