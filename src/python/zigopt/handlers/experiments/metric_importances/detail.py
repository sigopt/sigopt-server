# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.numbers import is_nan
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.json.builder.metric_importances import MetricImportancesJsonBuilder
from zigopt.json.builder.paging import PaginationJsonBuilder
from zigopt.net.errors import UnprocessableEntityError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class MetricImportancesDetailHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def importance_for_parameter_and_metric(self, experiment, parameter, metric):
    if len(experiment.all_parameters) <= 1:
      return 1

    if not experiment.experiment_meta.importance_maps:
      return None

    experiment_meta = experiment.experiment_meta
    importances = experiment_meta and experiment_meta.importance_maps.get(metric.name)
    metric_importance = importances and importances.importances.get(parameter.name)
    importance = metric_importance and metric_importance.importance
    return None if is_nan(importance) else importance

  def handle(self):
    assert self.experiment is not None

    data = []
    # NOTE: this expects that importances/service is also using all_metrics
    metrics = sorted(self.experiment.all_metrics, key=lambda m: m.name)

    for m in metrics:
      importances = {
        p.name: self.importance_for_parameter_and_metric(self.experiment, p, m) for p in self.experiment.all_parameters
      }

      if all(v is None for v in importances.values()):
        raise UnprocessableEntityError("Not enough observations to calculate parameter importances.")

      data.append(MetricImportancesJsonBuilder(m, importances))

    return PaginationJsonBuilder(data)
