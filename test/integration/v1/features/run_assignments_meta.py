# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.common.lists import recursively_omit_keys
from zigopt.handlers.validate.training_run import MAX_SOURCE_LENGTH
from zigopt.training_run.model import OPTIMIZED_ASSIGNMENT_SOURCE

from integration.base import RaisesApiException
from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META
from integration.v1.endpoints.training_runs.training_run_test_mixin import TrainingRunTestMixin
from integration.v1.test_base import V1Base


VALID_COMBOS = [
  ({"a": 1}, {"a": {"source": "source1"}}, {"source1": {"default_show": True, "sort": 1}}),
  ({"a": 1}, {"a": {"source": "source1"}}, {"source1": {"default_show": False, "sort": 88}}),
  (
    {"a": 1, "b": 2},
    {"a": {"source": "source1"}, "b": {"source": "source1"}},
    {"source1": {"default_show": True, "sort": 1}},
  ),
  (
    {"a": 1, "b": "string"},
    {"a": {"source": "source1"}},
    {"source1": {"default_show": True, "sort": 99}, "source2": {"default_show": False, "sort": 1}},
  ),
]


class TestTrainingRunsAssignmentsMeta(V1Base, TrainingRunTestMixin):
  @pytest.mark.parametrize("assignments, assignments_meta, assignments_sources", VALID_COMBOS)
  def test_basic_create(self, connection, project, assignments, assignments_meta, assignments_sources):

    run = (
      connection.clients(connection.client_id)
      .projects(project.id)
      .training_runs()
      .create(
        name="run",
        assignments=assignments,
        assignments_meta=assignments_meta,
        assignments_sources=assignments_sources,
      )
    )

    api_assignments = recursively_omit_keys(run.to_json()["assignments"], ["object"])
    api_assignments_meta = recursively_omit_keys(run.to_json()["assignments_meta"], ["object"])
    api_assignments_sources = recursively_omit_keys(run.to_json()["assignments_sources"], ["object"])

    assert assignments == api_assignments
    assert assignments_meta == api_assignments_meta
    assert assignments_sources == api_assignments_sources

  @pytest.mark.parametrize("assignments, assignments_meta, assignments_sources", VALID_COMBOS)
  def test_basic_updates(self, connection, project, assignments, assignments_meta, assignments_sources):

    created_run = (
      connection.clients(connection.client_id)
      .projects(project.id)
      .training_runs()
      .create(
        name="run",
      )
    )

    updated_run = connection.training_runs(created_run.id).merge(
      assignments=assignments,
      assignments_meta=assignments_meta,
      assignments_sources=assignments_sources,
    )

    api_assignments = recursively_omit_keys(updated_run.to_json()["assignments"], ["object"])
    api_assignments_meta = recursively_omit_keys(updated_run.to_json()["assignments_meta"], ["object"])
    api_assignments_sources = recursively_omit_keys(updated_run.to_json()["assignments_sources"], ["object"])

    assert assignments == api_assignments
    assert assignments_meta == api_assignments_meta
    assert assignments_sources == api_assignments_sources

  def test_sigopt_optmized_source(self, connection, project):
    ai_experiment = (
      connection.clients(project.client).projects(project.id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)
    )
    run = (
      connection.aiexperiments(ai_experiment.id)
      .training_runs()
      .create(
        name="run",
      )
    )
    ai_experiment_assignments = [p.name for p in ai_experiment.parameters]
    assignments_meta = run.to_json()["assignments_meta"]
    assignments_sources = run.to_json()["assignments_sources"]
    assert assignments_sources[OPTIMIZED_ASSIGNMENT_SOURCE]["sort"] == 1
    assert assignments_sources[OPTIMIZED_ASSIGNMENT_SOURCE]["default_show"] is True
    assert {key for key, value in assignments_meta.items() if value["source"] == OPTIMIZED_ASSIGNMENT_SOURCE} == set(
      ai_experiment_assignments
    )

  def test_sigopt_optmized_source_block_user(self, connection, project):
    assignments = {"x": 1}
    assignments_meta = {"x": {"source": OPTIMIZED_ASSIGNMENT_SOURCE}}

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      (
        connection.clients(connection.client_id)
        .projects(project.id)
        .training_runs()
        .create(name="run", assignments=assignments, assignments_meta=assignments_meta)
      )

    created_run = (
      connection.clients(connection.client_id)
      .projects(project.id)
      .training_runs()
      .create(name="run", assignments=assignments)
    )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.training_runs(created_run.id).merge(
        assignments_meta=assignments_meta,
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.training_runs(created_run.id).update(
        assignments_meta=assignments_meta,
      )

  def test_add_meta_for_param_doesnt_exist(self, connection, project):
    assignments = {"x": 1}
    assignments_meta = {"y": {"source": "abc"}}

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      (
        connection.clients(connection.client_id)
        .projects(project.id)
        .training_runs()
        .create(name="run", assignments=assignments, assignments_meta=assignments_meta)
      )

    created_run = (
      connection.clients(connection.client_id)
      .projects(project.id)
      .training_runs()
      .create(name="run", assignments=assignments)
    )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      (
        connection.training_runs(created_run.id).merge(
          assignments_meta=assignments_meta,
        )
      )

  def test_add_meta_for_param_does_exist(self, connection, project):
    assignments = {"x": 1}
    assignments_meta = {"x": {"source": "abc"}}

    created_run = (
      connection.clients(connection.client_id)
      .projects(project.id)
      .training_runs()
      .create(name="run", assignments=assignments)
    )

    updated_run = connection.training_runs(created_run.id).merge(
      assignments_meta=assignments_meta,
    )

    api_assignments_meta = recursively_omit_keys(updated_run.to_json()["assignments_meta"], ["object"])
    assert assignments_meta == api_assignments_meta

  def test_source_length_too_long(self, connection, project):
    TOO_LONG = "a" * (MAX_SOURCE_LENGTH + 1)
    assignments = {"x": 1}
    assignments_meta = {"x": {"source": TOO_LONG}}
    assignments_sources = {TOO_LONG: {"default_show": True, "sort": 1}}

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      (
        connection.clients(connection.client_id)
        .projects(project.id)
        .training_runs()
        .create(name="run", assignments=assignments, assignments_meta=assignments_meta)
      )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      (
        connection.clients(connection.client_id)
        .projects(project.id)
        .training_runs()
        .create(name="run", assignments=assignments, assignments_sources=assignments_sources)
      )
