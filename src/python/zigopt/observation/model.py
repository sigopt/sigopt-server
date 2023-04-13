# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Column, ForeignKey, Index
from sqlalchemy.orm import validates

from zigopt.common import *
from zigopt.assignments.model import HasAssignmentsMap
from zigopt.data.model import BaseHasMeasurementsProxy
from zigopt.db.column import ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData, ObservationValue


class ObservationDataProxy(HasAssignmentsMap, BaseHasMeasurementsProxy):
  def sorted_measurements(self):
    if self.reported_failure:
      return []
    if self.values:
      for v in self.values:
        if v.name == "":
          v.ClearField("name")
      return sorted(self.values, key=lambda val: val.name)
    return [(ObservationValue(value=None, value_var=None))]


class Observation(Base):
  __tablename__ = "observations"

  id = Column(BigInteger, primary_key=True)
  experiment_id = Column(BigInteger, ForeignKey("experiments.id", ondelete="CASCADE"))
  processed_suggestion_id = Column(
    BigInteger,
    ForeignKey("suggestions_processed.suggestion_id", ondelete="CASCADE"),
    index=True,
  )
  data = ProtobufColumn(ObservationData, proxy=ObservationDataProxy, name="data_json", nullable=False)

  def __init__(self, *args, **kwargs):
    kwargs["data"] = kwargs.get("data", Observation.data.default_value())
    super().__init__(*args, **kwargs)

  @validates("data")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta, proxy=ObservationDataProxy)

  __table_args__ = tuple(
    [
      Index("e-o-index", "experiment_id", "id"),
    ]
  )

  def __str__(self):
    return (
      "Observation("
      f"id={self.id},"
      f" experiment_id={self.experiment_id},"
      f" processed_suggestion_id={self.processed_suggestion_id},"
      f" data={self.data}"
      ")"
    )

  @property
  def data_proxy(self) -> ObservationDataProxy:
    """Explicitly returns ObservationDataProxy which helps with linting"""
    return ObservationDataProxy(self.data.underlying)  # pylint: disable=protobuf-undefined-attribute

  @property
  def reported_failure(self):
    return self.data.reported_failure

  @property
  def timestamp(self):
    return self.data.GetFieldOrNone("timestamp")  # pylint: disable=protobuf-undefined-attribute

  @property
  def client_provided_data(self):
    return self.data.GetFieldOrNone("client_provided_data")  # pylint: disable=protobuf-undefined-attribute

  @property
  def deleted(self):
    return self.data.deleted

  @property
  def values(self):
    return self.data.values

  @property
  def task(self):
    return self.data.GetFieldOrNone("task")  # pylint: disable=protobuf-undefined-attribute

  @property
  def has_suggestion(self):
    return self.processed_suggestion_id is not None

  def get_all_measurements(self, experiment):
    return self.data_proxy.get_all_measurements(experiment)

  def get_all_measurements_for_maximization(self, experiment):
    return self.data_proxy.get_all_measurements_for_maximization(experiment)

  def get_optimized_measurements_for_maximization(self, experiment):
    return self.data_proxy.get_optimized_measurements_for_maximization(experiment)

  def value_for_maximization(self, experiment, name):
    return self.data_proxy.value_for_maximization(experiment, name)

  def _within_metric_threshold(self, metric, experiment):
    metric_value = self.metric_value(experiment, metric.name)
    if metric_value is None:
      return False
    if metric.threshold is None:
      return True
    if metric.is_maximized:
      return metric_value >= metric.threshold
    if metric.is_minimized:
      return metric_value <= metric.threshold
    raise Exception("Unknown objective found while checking if observation is within metric thresholds")

  def within_metric_thresholds(self, experiment):
    return all(self._within_metric_threshold(metric, experiment) for metric in experiment.all_metrics)

  def metric_value(self, experiment, name):
    return self.data_proxy.metric_value(experiment, name)

  def metric_value_var(self, experiment, name):
    return self.data_proxy.metric_value_var(experiment, name)

  def get_assignment(self, parameter):
    return self.data_proxy.get_assignment(parameter)

  def get_assignments(self, experiment):
    return self.data_proxy.get_assignments(experiment)
