# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.project.model import Project
from zigopt.protobuf.dict import dict_to_protobuf_struct
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import (
  Dataset,
  Log,
  SourceCode,
  TrainingRunData,
  TrainingRunModel,
  TrainingRunValue,
)
from zigopt.training_run.model import TrainingRun

from integration.v1.test_base import V1Base


class TestTrainingRunsDetail(V1Base):
  def test_detail(self, services, connection, project):
    db_project = services.database_service.one(
      services.database_service.query(Project)
      .filter(Project.client_id == connection.client_id)
      .filter(Project.reference_id == project.id)
    )
    db_training_run = TrainingRun(
      client_id=connection.client_id,
      project_id=db_project.id,
      created_by=connection.user_id,
      training_run_data=TrainingRunData(
        datasets={
          "iris": Dataset(),
        },
        favorite=True,
        source_code=SourceCode(
          content='print("hello")',
          hash="abcdef",
        ),
        logs={
          "stdout": Log(
            content="",
          ),
        },
        assignments_struct=dict_to_protobuf_struct(
          dict(
            learning_rate=0.9,
          )
        ),
        training_run_model=TrainingRunModel(
          type="xgboost",
        ),
        name="Test training run",
        state=TrainingRunData.ACTIVE,
        values_map={
          "accuracy": TrainingRunValue(value=0.9, value_var=0.01),
        },
        metadata=dict_to_protobuf_struct(
          dict(
            metadata_string="abc",
            metadata_double=1.0,
          )
        ),
      ),
    )
    self.services.database_service.insert(db_training_run)
    training_run = connection.training_runs(db_training_run.id).fetch()

    assert len(training_run.assignments) == 1
    assert training_run.assignments["learning_rate"] == 0.9
    assert training_run.checkpoint_count == 0
    assert training_run.client == connection.client_id
    assert training_run.created <= unix_timestamp()
    assert len(training_run.datasets) == 1
    assert training_run.datasets["iris"] == {"object": "dataset"}
    assert training_run.deleted is False
    assert training_run.experiment is None
    assert training_run.favorite is True
    assert training_run.finished is False
    assert int(training_run.id) == db_training_run.id
    assert len(training_run.logs) == 1
    assert training_run.logs["stdout"]["content"] == ""
    assert len(training_run.metadata) == 2
    assert training_run.metadata["metadata_double"] == 1.0
    assert training_run.metadata["metadata_string"] == "abc"
    assert training_run.model.type == "xgboost"
    assert training_run.name == "Test training run"
    assert training_run.observation is None
    assert training_run.project is None
    assert training_run.project is None
    assert training_run.source_code.hash == "abcdef"
    assert training_run.source_code.content == 'print("hello")'
    assert training_run.state == "active"
    assert training_run.suggestion is None
    assert training_run.updated <= unix_timestamp()
    assert training_run.user == connection.user_id
    assert len(training_run.values) == 1
    assert training_run.values["accuracy"]["value"] == 0.9
    assert training_run.values["accuracy"]["value_stddev"] == 0.1
