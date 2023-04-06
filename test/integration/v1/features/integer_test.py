# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.sigoptcompute.constant import MINIMUM_SUCCESSES_TO_COMPUTE_EI

from integration.base import RaisesApiException
from integration.utils.random_assignment import random_assignments
from integration.v1.test_base import V1Base


class TestIntegerExperiments(V1Base):
  @pytest.mark.skip(
    reason=(
      "Need to change this test because 1. we should not be testing that we raise an internal server error 2."
      " switching to using queues in integration tests means SigoptComputeError cannot be exposed through"
      " the API"
    )
  )
  @pytest.mark.slow
  def test_optimize_integers(self, connection):
    experiment = (
      connection.clients(connection.client_id)
      .experiments()
      .create(
        name="Integer test",
        parameters=[dict(name="integer_parameter", bounds=dict(min=-1, max=0), type="int")],
      )
    )

    # TODO(SN-1141): Better way to ensure we're seeing a soft exception and not a crash
    with RaisesApiException(HTTPStatus.INTERNAL_SERVER_ERROR) as e:
      for _ in range(MINIMUM_SUCCESSES_TO_COMPUTE_EI + 1):
        connection.experiments(experiment.id).observations().create(
          assignments=random_assignments(experiment),
          value=0,
          no_optimize=False,
        )
    assert "GP failed to generate enough suggestions" in str(e)
