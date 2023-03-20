# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Index
from sqlalchemy.orm import validates

from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.db.column import ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.queued_suggestion.queued_suggestion_meta_pb2 import QueuedSuggestionMeta
from zigopt.protobuf.proxy import Proxy
from zigopt.suggestion.unprocessed.model import SuggestionDataProxy


class QueuedSuggestionMetaProxy(Proxy):
  def __init__(self, underlying):
    super().__init__(underlying)
    self._suggestion_data = SuggestionDataProxy(self.underlying.suggestion_data)

  @property
  def suggestion_data(self):
    return self._suggestion_data

  def get_assignments(self, experiment):
    return self.suggestion_data and self.suggestion_data.get_assignments(experiment)


class QueuedSuggestion(Base):
  __tablename__ = "suggestions_queued"
  id = Column(BigInteger, primary_key=True)
  claimed = Column(Boolean, default=False)
  created_time = Column(BigInteger)
  experiment_id = Column(BigInteger, ForeignKey("experiments.id", ondelete="CASCADE"))
  meta = ProtobufColumn(QueuedSuggestionMeta, proxy=QueuedSuggestionMetaProxy, name="meta_json")

  @validates("meta")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta, proxy=QueuedSuggestionMetaProxy)

  # Needs to be at bottom because it references a column
  __table_args__ = tuple(
    [
      Index("suggestions-queued-experiment-index", "experiment_id"),
    ]
  )

  def __init__(self, *args, **kwargs):
    kwargs["meta"] = kwargs.get("meta", QueuedSuggestion.meta.default_value())
    super().__init__(*args, **kwargs)
    if self.created_time is None:
      self.created_time = unix_timestamp()

  def __str__(self):
    return (
      f"QueuedSuggestion(id={self.id}, "
      f"experiment_id={self.experiment_id}, "
      f"claimed={self.claimed}, "
      f"created_time={self.created_time}, "
      f"meta={self.meta})"
    )

  def get_assignments(self, experiment):
    return self.meta.get_assignments(experiment)

  @property
  def task(self):
    return self.meta.suggestion_data.task
