# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy
from typing import Any

import pytest

from zigopt.experiment.constant import MetricStrategyNames


class StoredMetricsMixin:
  offline_experiment_meta: dict[str, Any]

  @pytest.fixture
  def optimized_metric_name(self):
    return "optimized-metric"

  @pytest.fixture
  def stored_metric_name(self):
    return "stored-metric"

  @pytest.fixture
  def experiment(self, connection, optimized_metric_name, stored_metric_name):
    e_meta = deepcopy(self.offline_experiment_meta)
    e_meta["metrics"] = [
      dict(name=optimized_metric_name),
      dict(name=stored_metric_name, strategy=MetricStrategyNames.STORE),
    ]
    return connection.create_experiment(e_meta)

  @pytest.fixture
  def suggestion(self, connection, experiment):
    return connection.experiments(experiment.id).suggestions().create()
