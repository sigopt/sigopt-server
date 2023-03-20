# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common.sigopt_datetime import current_datetime
from zigopt.experiment.model import Experiment
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *

from integration.service.test_base import ServiceBase


class ExperimentServiceTestBase(ServiceBase):
  @pytest.fixture
  def experiment(self, client):
    now = current_datetime()
    return Experiment(
      client_id=client.id,
      date_created=now,
      date_updated=now,
      name="test experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=[
          ExperimentParameter(name="p1", param_type=PARAMETER_DOUBLE, bounds=Bounds(minimum=-10, maximum=10))
        ],
        conditionals=[ExperimentConditional(name="c1", values=[ExperimentConditionalValue(name="cv1")])],
        observation_budget=60,
        development=False,
      ),
    )
