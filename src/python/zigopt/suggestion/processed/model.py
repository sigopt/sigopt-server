# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Index
from sqlalchemy.orm import validates

from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.db.column import ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.suggest.suggestion_pb2 import ProcessedSuggestionMeta


class ProcessedSuggestion(Base):
  __tablename__ = "suggestions_processed"
  # __table_args__ is below

  experiment_id = Column(BigInteger, ForeignKey("experiments.id", ondelete="CASCADE"))
  suggestion_id = Column(BigInteger, ForeignKey("suggestions.id", ondelete="CASCADE"), index=True, primary_key=True)
  queued_id = Column(BigInteger, unique=True)
  processed_suggestion_meta = ProtobufColumn(ProcessedSuggestionMeta, name="processed_suggestion_meta_json")

  # the timestamp this suggestion was processed
  processed_time = Column(BigInteger)
  deleted = Column(Boolean(), default=False)
  # the suggestion was created automatically ie. not via the suggestion create endpoint
  automatic = Column(Boolean, default=False)

  @validates("processed_suggestion_meta")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta)

  # Needs to be at bottom because it references a column
  __table_args__ = tuple((Index("processed-main-index", "experiment_id", "processed_time"),))

  def __init__(self, *args, **kwargs):
    kwargs["processed_suggestion_meta"] = kwargs.get(
      "processed_suggestion_meta",
      ProcessedSuggestion.processed_suggestion_meta.default_value(),
    )
    super().__init__(*args, **kwargs)
    if self.processed_time is None:
      self.processed_time = unix_timestamp()

  def __str__(self):
    return (
      "ProcessedSuggestion("
      f"experiment_id={self.experiment_id}, "
      f"suggestion_id={self.suggestion_id}, "
      f"queued_id={self.queued_id}, "
      f"processed_time={self.processed_time}, "
      f"deleted={self.deleted}, "
      f"processed_suggestion_meta={self.processed_suggestion_meta}"
      ")"
    )

  @property
  def client_provided_data(self):
    if self.processed_suggestion_meta.HasField("client_provided_data"):
      return self.processed_suggestion_meta.client_provided_data
    return None
