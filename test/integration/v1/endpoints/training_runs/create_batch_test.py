# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus
from typing import Any

import pytest

from zigopt.handlers.training_runs.create import MAX_RUNS_BATCH_CREATE_COUNT

from integration.base import RaisesApiException
from integration.v1.endpoints.training_runs.training_run_test_mixin import TrainingRunTestMixin
from integration.v1.test_base import V1Base


class TestTrainingRunsBatchCreate(V1Base, TrainingRunTestMixin):
  def create_run(self, n):
    return {
      "name": f"batch-{n}",
      "assignments": {
        "x": n,
        "y": n * n,
      },
      "values": {
        "r0": dict(value=n * n + n),
        "r1": dict(value=n**2),
      },
      "state": "completed" if (n % 2 == 0) else "failed",
    }

  @pytest.mark.parametrize("verbose", [True, False])
  def test_create_batch(self, connection, project, verbose, n=10):
    runs = [self.create_run(i) for i in range(n)]
    args: dict[str, Any] = dict(runs=runs)
    if not verbose:
      args["fields"] = "id,state"
    training_runs = (
      connection.clients(connection.client_id).projects(project.id).training_runs().create_batch(**args).data
    )
    assert len(training_runs) == n
    if verbose:
      for a, b in zip(training_runs, runs):
        assert a.name == b["name"]
        assert a.assignments["x"] == b["assignments"]["x"]
        assert a.assignments["y"] == b["assignments"]["y"]
        assert a.values["r0"]["value"] == b["values"]["r0"]["value"]
        assert a.values["r1"]["value"] == b["values"]["r1"]["value"]
        assert a.state == b["state"]
    else:
      for a in training_runs:
        assert a.id is not None
        assert a.name is None
        assert a.assignments is None
        assert a.values is None
        assert a.state is not None

  def test_limit_batch_size(self, connection, project):
    runs = [self.create_run(i) for i in range(MAX_RUNS_BATCH_CREATE_COUNT + 1)]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).projects(project.id).training_runs().create_batch(runs=runs)
