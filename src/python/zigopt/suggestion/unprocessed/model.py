# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import uuid

from sqlalchemy import BigInteger, Column, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates

from zigopt.assignments.model import HasAssignmentsMap
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.db.column import ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData, SuggestionMeta
from zigopt.protobuf.proxy import Proxy


class SuggestionDataProxy(HasAssignmentsMap):
  def __init__(self, underlying):
    super().__init__(underlying)


class SuggestionMetaProxy(Proxy):
  def __init__(self, underlying):
    super().__init__(underlying)

  @property
  def suggestion_data(self):
    real_suggestion_data = self.underlying.suggestion_data or (SuggestionData())
    return SuggestionDataProxy(real_suggestion_data)

  @property
  def deleted(self):
    return self.suggestion_data.deleted

  def get_assignment(self, parameter):
    return self.suggestion_data.get_assignment(parameter)

  def get_assignments(self, experiment):
    return self.suggestion_data.get_assignments(experiment)

  def get_conditional_assignments(self, experiment):
    return self.suggestion_data.get_conditional_assignments(experiment)


SUGGESTIONS_ID_SEQUENCE_NAME = "suggestions_id_seq"
SUGGESTIONS_UUID_CONSTRAINT_NAME = "suggestions_uuid_value_unique_constraint"


def source_to_string(source):
  source_to_string_map = {
    UnprocessedSuggestion.Source.LATIN_HYPERCUBE: "latin hypercube",
    UnprocessedSuggestion.Source.USER_CREATED: "user created",
    UnprocessedSuggestion.Source.GRID: "grid",
    UnprocessedSuggestion.Source.QUEUED_SUGGESTION: "queued suggestion",
    UnprocessedSuggestion.Source.SPE: "spe",
    UnprocessedSuggestion.Source.PADDING_RANDOM: "padding random",
    UnprocessedSuggestion.Source.EXPLICIT_RANDOM: "explicit random",
    UnprocessedSuggestion.Source.FALLBACK_RANDOM: "fallback random",
    UnprocessedSuggestion.Source.LOW_DISCREPANCY_RANDOM: "low discrepancy random",
    UnprocessedSuggestion.Source.GP_CATEGORICAL: "gp categorical",
    UnprocessedSuggestion.Source.HIGH_CONTENTION_RANDOM: "high contention random",
    UnprocessedSuggestion.Source.LOW_DISCREPANCY_DETERMINISTIC: "low discrepancy deterministic",
    UnprocessedSuggestion.Source.UNKNOWN_FALLBACK_RANDOM: "unknown fallback random",
    UnprocessedSuggestion.Source.CONFLICT_REPLACEMENT_RANDOM: "conflict replacement random",
    UnprocessedSuggestion.Source.SEARCH: "search",
    UnprocessedSuggestion.Source.XGB: "xgb metalearning prior",
    UnprocessedSuggestion.Source.SPE_SEARCH: "spe search",
  }
  return source_to_string_map[source]


class UnprocessedSuggestion(Base):
  class Source:
    LATIN_HYPERCUBE = 1
    USER_CREATED = 2
    GRID = 3
    QUEUED_SUGGESTION = 4
    SPE = 5
    PADDING_RANDOM = 6
    EXPLICIT_RANDOM = 7
    FALLBACK_RANDOM = 8
    LOW_DISCREPANCY_RANDOM = 9
    GP_CATEGORICAL = 10
    HIGH_CONTENTION_RANDOM = 11
    LOW_DISCREPANCY_DETERMINISTIC = 12
    UNKNOWN_FALLBACK_RANDOM = 13
    CONFLICT_REPLACEMENT_RANDOM = 14
    SEARCH = 15
    XGB = 16
    SPE_SEARCH = 17

    @classmethod
    def get_random_sources(cls):
      return [
        cls.EXPLICIT_RANDOM,
        cls.FALLBACK_RANDOM,
        cls.HIGH_CONTENTION_RANDOM,
        cls.LOW_DISCREPANCY_RANDOM,
        cls.PADDING_RANDOM,
        cls.UNKNOWN_FALLBACK_RANDOM,
        cls.CONFLICT_REPLACEMENT_RANDOM,
      ]

  __tablename__ = "suggestions"
  __table_args__ = tuple(
    [
      UniqueConstraint(
        "uuid_value",
        name=SUGGESTIONS_UUID_CONSTRAINT_NAME,
      ),
      Index("ix_experiment_id_source_date", "experiment_id", "source", "generated_time"),
    ]
  )

  id = Column(BigInteger, primary_key=True)
  experiment_id = Column(BigInteger, ForeignKey("experiments.id", ondelete="CASCADE"))
  source = Column(Integer)
  suggestion_meta = ProtobufColumn(
    SuggestionMeta,
    proxy=SuggestionMetaProxy,
    name="suggestion_meta_json",
    nullable=False,
  )
  generated_time = Column(BigInteger)
  uuid_value = Column(UUID(as_uuid=True))

  def __init__(self, *args, **kwargs):
    kwargs["suggestion_meta"] = kwargs.get("suggestion_meta", UnprocessedSuggestion.suggestion_meta.default_value())
    super().__init__(*args, **kwargs)
    if self.generated_time is None:
      self.generated_time = unix_timestamp()
    if self.uuid_value is None:
      self.uuid_value = uuid.uuid4()

  @validates("suggestion_meta")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta, proxy=SuggestionMetaProxy)

  def __str__(self):
    return (
      f"UnprocessedSuggestion(id={self.id}, experiment_id={self.experiment_id}, suggestion_meta={self.suggestion_meta})"
    )

  @property
  def deleted(self):
    return self.suggestion_meta.deleted

  def get_assignment(self, parameter):
    return self.suggestion_meta.get_assignment(parameter)

  def get_assignments(self, experiment):
    return self.suggestion_meta.get_assignments(experiment)

  def get_conditional_assignments(self, experiment):
    return self.suggestion_meta.get_conditional_assignments(experiment)

  def is_valid(self, experiment):
    # TODO(SN-1126): what does validity mean for conditionals?
    for (name, assignment) in self.get_assignments(experiment).items():
      parameter = experiment.all_parameters_map.get(name)
      if not parameter:
        if not experiment.conditionals_map.get(name):
          return False
      elif not parameter.valid_assignment(assignment):
        return False
    return True

  # TODO(RTL-125): Should this be a function that requires passing the experiment ??  Is None a good default ??
  @property
  def task(self):
    return self.suggestion_meta.suggestion_data.GetFieldOrNone("task")
