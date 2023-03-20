# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.training_run.constant import *

from integration.base import RaisesApiException
from integration.v1.endpoints.training_runs.training_run_test_mixin import TrainingRunTestMixin
from integration.v1.test_base import V1Base


class TestTrainingRunsCreate(V1Base, TrainingRunTestMixin):
  def test_basic_create(self, connection, project):
    now = unix_timestamp()
    training_run = connection.clients(connection.client_id).projects(project.id).training_runs().create(name="run")
    assert training_run.name == "run"
    assert training_run.client == connection.client_id
    assert training_run.user == connection.user_id
    assert training_run.project == project.id
    assert training_run.created >= now
    assert training_run.updated == training_run.created

  def test_required_name(self, connection, project):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).projects(project.id).training_runs().create()

  def test_invalid_project(self, connection, project):
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.clients(connection.client_id).projects("some fake project").training_runs().create(name="run")

  def test_create_with_project_key(self, connection, project):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(connection.client_id).projects(project.id).training_runs().create(
        name="run",
        project=project.id,
      )

  def test_invalid_client(self, connection, project):
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.clients("0").projects(project.id).training_runs().create(name="run")

  def test_basic_create_with_dev_token(self, development_connection, project):
    now = unix_timestamp()
    training_run = (
      development_connection.clients(development_connection.client_id)
      .projects(project.id)
      .training_runs()
      .create(name="run")
    )
    assert training_run.name == "run"
    assert training_run.project == project.id
    assert training_run.created >= now
    assert training_run.updated == training_run.created
