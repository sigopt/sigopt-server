# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.common.sigopt_datetime import current_datetime
from zigopt.experiment.model import Experiment
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentMeta
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import TrainingRunData
from zigopt.training_run.model import TrainingRun

from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META
from integration.v1.experiments_test_base import ExperimentsTestBase


class TestDetailExperiments(ExperimentsTestBase):
  def test_experiment_detail(self, connection):
    e = connection.create_any_experiment()
    detail = connection.experiments(e.id).fetch()
    assert detail.id == e.id

  def test_parameter_order(self, connection, client_id):
    e = (
      connection.clients(client_id)
      .experiments()
      .create(
        name="Test Experiments",
        parameters=[
          dict(name="z", type="double", bounds=dict(min=0, max=1)),
          dict(
            name="a",
            type="categorical",
            categorical_values=[
              dict(enum_index=1, name="c"),
              dict(enum_index=2, name="w"),
              dict(enum_index=3, name="h"),
            ],
          ),
          dict(name="d", type="int", bounds=dict(min=0, max=1)),
        ],
      )
    )
    e = connection.experiments(e.id).fetch()
    assert [p.name for p in e.parameters] == ["a", "d", "z"]

  def create_run(self, experiment, finished, state):
    run_data = TrainingRunData()
    run_data.state = state
    run = TrainingRun(
      completed=current_datetime() if finished else None,
      client_id=experiment.client_id,
      experiment_id=experiment.id,
      training_run_data=run_data,
    )
    return run

  def test_run_progress(self, services, connection):
    experiment_meta = ExperimentMeta()
    experiment_meta.observation_budget = 15
    experiment_meta.runs_only = True
    experiment = Experiment(experiment_meta=experiment_meta, client_id=connection.client_id)
    db_service = services.database_service
    db_service.insert(experiment)

    runs: list[TrainingRun] = []
    runs.extend(self.create_run(experiment, False, TrainingRunData.ACTIVE) for _ in range(2))
    runs.extend(self.create_run(experiment, True, TrainingRunData.COMPLETED) for _ in range(4))
    runs.extend(self.create_run(experiment, True, TrainingRunData.FAILED) for _ in range(8))
    db_service.insert_all(runs)

    e = connection.experiments(experiment.id).fetch()
    progress_data = e.progress.to_json()
    assert progress_data["object"] == "progress"
    assert progress_data["active_run_count"] == 2
    assert progress_data["finished_run_count"] == 12
    assert progress_data["total_run_count"] == 14
    assert progress_data["remaining_budget"] == 1

  @pytest.fixture
  def ai_experiment(self, connection, project):
    return connection.clients(project.client).projects(project.id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)

  def test_ai_experiment_redirect(self, services, connection, ai_experiment):
    response = connection.raw_request("GET", f"/v1/experiments/{ai_experiment.id}")
    assert response.status_code == HTTPStatus.OK
    assert response.url.endswith(f"/v1/aiexperiments/{ai_experiment.id}")
    e = connection.experiments(ai_experiment.id).fetch()
    assert e.to_json()["object"] == "aiexperiment"
    assert e.id == ai_experiment.id
