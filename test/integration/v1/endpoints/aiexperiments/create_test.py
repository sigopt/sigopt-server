# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from http import HTTPStatus

import pytest

from integration.base import RaisesApiException
from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META
from integration.v1.experiments_test_base import AiExperimentsTestBase


class TestCreateAiExperiments(AiExperimentsTestBase):
  def create_ai_experiment(self, connection, project, meta):
    return connection.clients(project.client).projects(project.id).aiexperiments().create(**meta)

  def test_experiment_create(self, connection, project, any_meta):
    e = self.create_ai_experiment(connection, project, any_meta)
    assert e.id is not None
    assert set(any_meta) <= set(e.to_json())

  @pytest.mark.parametrize(
    "removed_field",
    [
      "metrics",
      "name",
      "parameters",
    ],
  )
  def test_experiment_create_invalid_missing_field(self, removed_field, connection, project):
    meta = copy.deepcopy(DEFAULT_AI_EXPERIMENT_META)
    del meta[removed_field]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.create_ai_experiment(connection, project, meta)

  def test_experiment_create_extra_parameters(self, connection, project, any_meta):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.create_ai_experiment(connection, project, {"foo": "bar", **any_meta})

  def test_development_token_disallowed(self, development_connection, connection, project):
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.create_ai_experiment(development_connection, project, DEFAULT_AI_EXPERIMENT_META)

  def test_create_progress(self, connection, project):
    experiment = self.create_ai_experiment(connection, project, DEFAULT_AI_EXPERIMENT_META)
    progress_data = experiment.progress
    assert progress_data.active_run_count == 0
    assert progress_data.finished_run_count == 0
    assert progress_data.total_run_count == 0
    assert progress_data.remaining_budget == DEFAULT_AI_EXPERIMENT_META["budget"]

  def test_create_invalid_client(self, connection):
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.clients("0").projects("sigopt-examples").aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)

  def test_create_invalid_project(self, connection, client_id):
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.clients(client_id).projects("invalid-project").aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)

  @pytest.mark.parametrize(
    "budget",
    [
      None,
      1,
      100,
    ],
  )
  def test_create_valid_budget(self, connection, project, budget):
    experiment = self.create_ai_experiment(
      connection,
      project,
      {
        **DEFAULT_AI_EXPERIMENT_META,
        "budget": budget,
      },
    )
    assert experiment.budget == budget

  @pytest.mark.parametrize(
    "budget",
    [
      -1,
      0,
      "1",
      [],
      {},
    ],
  )
  def test_create_invalid_budget(self, connection, project, budget):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.create_ai_experiment(
        connection,
        project,
        {
          **DEFAULT_AI_EXPERIMENT_META,
          "budget": budget,
        },
      )

  @pytest.mark.parametrize(
    "metrics,expected_names",
    [
      (["m1"], ["m1"]),
      (["m1", "m2"], ["m1", "m2"]),
    ],
  )
  def test_create_metrics(self, connection, project, metrics, expected_names):
    e = self.create_ai_experiment(
      connection,
      project,
      {
        **DEFAULT_AI_EXPERIMENT_META,
        "metrics": [{"name": name} for name in metrics],
      },
    )
    assert [m.name for m in e.metrics] == expected_names
