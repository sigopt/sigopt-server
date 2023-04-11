# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from datetime import timedelta

import pytest

from zigopt.common import remove_nones
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.common.strings import random_string
from zigopt.experiment.model import Experiment
from zigopt.project.model import MAX_ID_LENGTH as MAX_PROJECT_ID_LENGTH
from zigopt.project.model import Project
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentMeta

from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META
from integration.v1.experiments_test_base import ExperimentsTestBase


class TestListAiExperiments(ExperimentsTestBase):
  def make_project(self, services, connection, name):
    return services.project_service.insert(
      Project(
        name=name,
        reference_id=random_string(MAX_PROJECT_ID_LENGTH).lower(),
        client_id=connection.client_id,
        created_by=None,
      )
    )

  @pytest.fixture
  def project1(self, services, connection):
    return self.make_project(services, connection, "Test AiExperiment List Project 1")

  @pytest.fixture
  def project2(self, services, connection):
    return self.make_project(services, connection, "Test AiExperiment List Project 2")

  def test_single(self, connection, project1):
    e = (
      connection.clients(project1.client_id)
      .projects(project1.reference_id)
      .aiexperiments()
      .create(**DEFAULT_AI_EXPERIMENT_META)
    )
    for func in (
      connection.as_client_only().aiexperiments().fetch,
      connection.clients(project1.client_id).projects(project1.reference_id).aiexperiments().fetch,
    ):
      paging = func()
      assert paging.count == 1
      assert paging.paging.before is None
      assert len(paging.data) == 1
      assert paging.data[0].id == e.id

  @pytest.mark.parametrize(
    "sort_field,order",
    [
      (None, [0, 1]),
      ("id", [0, 1]),
      ("recent", [1, 0]),
    ],
  )
  @pytest.mark.parametrize(
    "ascending",
    [
      True,
      False,
      None,
    ],
  )
  def test_sort(self, services, connection, project1, sort_field, order, ascending):
    e1 = (
      connection.clients(project1.client_id)
      .projects(project1.reference_id)
      .aiexperiments()
      .create(**DEFAULT_AI_EXPERIMENT_META)
    )
    e2 = (
      connection.clients(project1.client_id)
      .projects(project1.reference_id)
      .aiexperiments()
      .create(**DEFAULT_AI_EXPERIMENT_META)
    )
    date = current_datetime()
    for e, updated in [
      (e1, date + timedelta(minutes=1)),
      (e2, date),
    ]:
      services.database_service.update(
        services.database_service.query(Experiment).filter(Experiment.id == e.id),
        {Experiment.date_updated: updated},
      )
    experiments = [e1, e2]
    params = {"ascending": ascending, "sort": sort_field}
    if not ascending:
      order = order[::-1]
    for func in (
      connection.as_client_only().aiexperiments().fetch,
      connection.clients(project1.client_id).projects(project1.reference_id).aiexperiments().fetch,
    ):
      paging = func(**remove_nones(params))
      assert paging.count == 2
      if ascending:
        assert paging.paging.after is None
      else:
        assert paging.paging.before is None
      assert len(paging.data) == 2
      for data_index, experiment_index in enumerate(order):
        assert paging.data[data_index].id == experiments[experiment_index].id

  @pytest.mark.parametrize(
    "ascending",
    [
      True,
      False,
    ],
  )
  def test_paging(self, services, connection, project1, ascending):
    e1 = (
      connection.clients(project1.client_id)
      .projects(project1.reference_id)
      .aiexperiments()
      .create(**DEFAULT_AI_EXPERIMENT_META)
    )
    e2 = (
      connection.clients(project1.client_id)
      .projects(project1.reference_id)
      .aiexperiments()
      .create(**DEFAULT_AI_EXPERIMENT_META)
    )
    params = {"ascending": ascending, "limit": 1}
    for func in (
      connection.as_client_only().aiexperiments().fetch,
      connection.clients(project1.client_id).projects(project1.reference_id).aiexperiments().fetch,
    ):
      page = func(**remove_nones(params))
      assert page.count == 2
      assert len(page.data) == 1
      ids = [page.data[0].id]
      next_page_params = {**params}
      if ascending:
        next_page_params["after"] = page.paging.after
      else:
        next_page_params["before"] = page.paging.before
      page = func(**remove_nones(next_page_params))
      assert page.count == 2
      assert len(page.data) == 1
      if ascending:
        assert page.paging.after is None
      else:
        assert page.paging.before is None
      ids.append(page.data[0].id)
      if ascending:
        assert ids == [e1.id, e2.id]
      else:
        assert ids == [e2.id, e1.id]

  @pytest.mark.parametrize(
    "search_term,expected_results",
    [
      ("", [0, 1]),
      ("Hello", [0, 1]),
      ("hello", [0, 1]),
      ("there", [1]),
      ("hello there", [1]),
      ("asdf", []),
    ],
  )
  def test_search(self, services, connection, project1, search_term, expected_results):
    e1 = (
      connection.clients(project1.client_id)
      .projects(project1.reference_id)
      .aiexperiments()
      .create(**{**DEFAULT_AI_EXPERIMENT_META, "name": "Hello World"})
    )
    e2 = (
      connection.clients(project1.client_id)
      .projects(project1.reference_id)
      .aiexperiments()
      .create(**{**DEFAULT_AI_EXPERIMENT_META, "name": "hello there"})
    )
    expected_results = [[e1.id, e2.id][r] for r in reversed(expected_results)]
    params = {"search": search_term}
    for func in (
      connection.as_client_only().aiexperiments().fetch,
      connection.clients(project1.client_id).projects(project1.reference_id).aiexperiments().fetch,
    ):
      page = func(**params)
      assert page.count == len(expected_results)
      assert len(page.data) == len(expected_results)
      actual_results = [e.id for e in page.data]
      assert actual_results == expected_results

  def test_development(self, connection, services, project1):
    experiment_meta = ExperimentMeta()
    experiment_meta.observation_budget = 15
    experiment_meta.runs_only = True
    experiment_meta.development = True
    experiment = Experiment(experiment_meta=experiment_meta, client_id=project1.client_id, project_id=project1.id)
    services.database_service.insert(experiment)
    for func in (
      connection.as_client_only().aiexperiments().fetch,
      connection.clients(project1.client_id).projects(project1.reference_id).aiexperiments().fetch,
    ):
      paging = func()
      assert paging.count == 1
      assert paging.paging.before is None
      assert len(paging.data) == 1
      assert paging.data[0].id == str(experiment.id)

  def test_multiple_projects(self, connection, services, project1, project2):
    experiments = [
      [
        connection.clients(project.client_id)
        .projects(project.reference_id)
        .aiexperiments()
        .create(**DEFAULT_AI_EXPERIMENT_META)
        for _ in range(2)
      ]
      for project in (project1, project2)
    ]
    page = connection.as_client_only().aiexperiments().fetch()
    assert [e.id for e in reversed(page.data)] == [e.id for p_exps in experiments for e in p_exps]
    for i, project in enumerate([project1, project2]):
      page = connection.clients(project.client_id).projects(project.reference_id).aiexperiments().fetch()
      assert page.count == len(experiments[i])
      assert [e.id for e in reversed(page.data)] == [e.id for e in experiments[i]]
      assert all(e.project == project.reference_id for e in page.data)
