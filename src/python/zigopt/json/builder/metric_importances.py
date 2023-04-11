# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.common import *
from zigopt.json.builder.json_builder import JsonBuilder, ValidationType, field
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentMetric


class MetricImportancesJsonBuilder(JsonBuilder):
  object_name = "metric_importances"

  def __init__(self, metric: ExperimentMetric, metric_importances: dict[str, float]):
    self._metric = metric
    self._metric_importances = metric_importances

  @field(ValidationType.string)
  def metric(self) -> Optional[str]:
    if self._metric.name:
      return self._metric.name
    return None

  @field(ValidationType.object)
  def importances(self) -> dict[str, float]:
    return self._metric_importances
