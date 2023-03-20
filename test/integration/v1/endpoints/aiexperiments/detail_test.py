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

from integration.base import RaisesApiException
from integration.v1.constants import DEFAULT_EXPERIMENT_META
from integration.v1.experiments_test_base import AiExperimentsTestBase


class TestAiExperimentsDetail(AiExperimentsTestBase):
  @pytest.fixture
  def any_ai_experiment(self, connection, project, any_meta):
    return connection.clients(project.client).projects(project.id).aiexperiments().create(**any_meta)

  def test_ai_experiment_detail(self, connection, any_ai_experiment):
    e = any_ai_experiment
    detail = connection.aiexperiments(e.id).fetch()
    assert detail.id == e.id
    assert detail.metrics == e.metrics
    assert detail.parameters == e.parameters
    assert detail.progress == e.progress
    assert detail.budget == e.budget
    assert detail.name == e.name

  def test_detail_wrong_experiment_class(self, connection, project):
    e = connection.clients(connection.client_id).experiments().create(**DEFAULT_EXPERIMENT_META)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.aiexperiments(e.id).fetch()

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

    runs = [
      *(self.create_run(experiment, False, TrainingRunData.ACTIVE) for _ in range(2)),
      *(self.create_run(experiment, True, TrainingRunData.COMPLETED) for _ in range(4)),
      *(self.create_run(experiment, True, TrainingRunData.FAILED) for _ in range(8)),
    ]
    db_service.insert_all(runs)

    e = connection.aiexperiments(experiment.id).fetch()
    progress_data = e.progress.to_json()
    assert progress_data["object"] == "progress"
    assert progress_data["active_run_count"] == 2
    assert progress_data["finished_run_count"] == 12
    assert progress_data["total_run_count"] == 14
    assert progress_data["remaining_budget"] == 1
