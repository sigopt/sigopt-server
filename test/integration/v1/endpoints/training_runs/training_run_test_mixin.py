# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common.strings import random_string


class TrainingRunTestMixin:
  @pytest.fixture
  def project(self, connection):
    project_id = random_string(str_length=20).lower()
    return connection.clients(connection.client_id).projects().create(name=project_id, id=project_id)

  @pytest.fixture
  def training_run(self, connection, project):
    return connection.clients(connection.client_id).projects(project.id).training_runs().create(name="run")

  @pytest.fixture
  def aiexperiment_in_project(self, connection, project):
    return (
      connection.projects(project.id)
      .aiexperiments()
      .create(
        project=project.id,
        metrics=[dict(name="Accuracy", objective="maximize", strategy="optimize")],
        parameters=[
          {"name": "x", "type": "double", "bounds": {"min": 0, "max": 10}},
          {"name": "y", "type": "int", "bounds": {"min": -0, "max": 10}},
        ],
      )
    )
