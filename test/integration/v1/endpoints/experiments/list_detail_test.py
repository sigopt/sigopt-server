# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime
from http import HTTPStatus
from time import sleep

import pytest

from zigopt.api.paging import deserialize_paging_marker, serialize_paging_marker
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.common.strings import random_string
from zigopt.experiment.model import Experiment
from zigopt.handlers.experiments.list_base import EXPERIMENT_RECENCY
from zigopt.invite.constant import ADMIN_ROLE, NO_ROLE, USER_ROLE
from zigopt.project.model import MAX_ID_LENGTH as MAX_PROJECT_ID_LENGTH
from zigopt.project.model import Project
from zigopt.protobuf.gen.api.paging_pb2 import PagingMarker, PagingSymbol

from integration.base import RaisesApiException
from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META
from integration.v1.experiments_test_base import ExperimentsTestBase
from integration.v1.test_base import V1Connection


def id_from_paging_marker(serialized_marker):
  marker = deserialize_paging_marker(serialized_marker)
  symbol = marker.symbols[-1]
  assert symbol.WhichOneof("type") == "int_value"
  return str(symbol.int_value)


def paging_marker_from_id(_id):
  return serialize_paging_marker(PagingMarker(symbols=[PagingSymbol(int_value=int(_id))]))


class TestListExperiments(ExperimentsTestBase):
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
  def any_ai_experiment(self, connection, project, any_ai_experiment_meta):
    return connection.clients(project.client).projects(project.id).aiexperiments().create(**any_ai_experiment_meta)

  @pytest.fixture(params=["user", "client", "user-sort", "client-sort"])
  def fetcher(self, request, connection):
    if request.param == "client":
      return lambda *args, **kwargs: connection.clients(connection.client_id).experiments().fetch(*args, **kwargs)
    if request.param == "user":
      return lambda *args, **kwargs: connection.users(connection.user_id).experiments().fetch(*args, **kwargs)
    if request.param == "client-sort":

      def r(*args, **kwargs):
        kwargs["sort"] = kwargs.get("sort", EXPERIMENT_RECENCY)
        return connection.clients(connection.client_id).experiments().fetch(*args, **kwargs)

      return r
    if request.param == "user-sort":

      def r(*args, **kwargs):  # pylint: disable=function-redefined
        kwargs["sort"] = kwargs.get("sort", EXPERIMENT_RECENCY)
        return connection.users(connection.user_id).experiments().fetch(*args, **kwargs)

      return r
    return None

  def test_experiment_list_single(self, connection, fetcher):
    e = connection.create_any_experiment()
    paging = fetcher()
    assert paging.count == 1
    assert paging.paging.before is None
    assert id_from_paging_marker(paging.paging.after) == e.id
    assert len(paging.data) == 1
    assert paging.data[0].id == e.id

  def test_experiment_list_with_projects(self, services, connection, fetcher):
    project1 = self.make_project(
      services,
      connection,
      "test project for experiment list",
    )
    project2 = self.make_project(
      services,
      connection,
      "another test project for experiment list",
    )
    e1 = connection.create_any_experiment(project=project1.reference_id)
    e2 = connection.create_any_experiment(project=project2.reference_id)
    paging = fetcher()
    assert paging.count == 2
    assert paging.paging.before is None
    assert id_from_paging_marker(paging.paging.after) == e2.id
    assert len(paging.data) == 2
    assert paging.data[0].id == e2.id
    assert paging.data[0].project == project2.reference_id
    assert paging.data[1].id == e1.id
    assert paging.data[1].project == project1.reference_id

  def test_experiment_list_all(self, connection: V1Connection, fetcher):
    e1, e2, e3 = (connection.create_any_experiment() for _ in range(3))
    paging = fetcher()
    assert paging.count == 3
    assert paging.paging.before is None
    assert id_from_paging_marker(paging.paging.after) == e3.id
    assert len(paging.data) == 3
    assert [d.id for d in paging.data] == [e3.id, e2.id, e1.id]

  def test_experiments_list_omit_development(self, connection, development_connection, fetcher):
    for _ in range(2):
      connection.create_any_experiment()
    dev = development_connection.create_any_experiment()
    paging = fetcher()
    assert paging.count == 3
    paging = fetcher(development=True)
    assert paging.count == 1
    assert dev.id in [e.id for e in paging.data]
    paging = fetcher(development=False)
    assert paging.count == 2
    assert dev.id not in [e.id for e in paging.data]

  def test_experiments_list_omit_ai(self, connection, project, fetcher):
    ai_experiment = (
      connection.clients(project.client).projects(project.id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)
    )
    for _ in range(2):
      connection.create_any_experiment()
    paging = fetcher()
    assert paging.count == 2
    paging = fetcher(include_ai=True)
    assert paging.count == 3
    assert ai_experiment.id in [e.id for e in paging.data]
    found_ai_experiment = next(e for e in paging.data if e.id == ai_experiment.id)
    assert found_ai_experiment.to_json()["object"] == "aiexperiment"
    paging = fetcher(include_ai=False)
    assert paging.count == 2
    assert ai_experiment.id not in [e.id for e in paging.data]

  def test_experiment_list_private(self, connection, client_id, config_broker, api, auth_provider, inbox):
    other_connection = self.make_v1_connection(config_broker, api, auth_provider)
    other_user = other_connection.users(other_connection.user_id).fetch()
    connection.clients(client_id).invites().create(email=other_user.email, role=USER_ROLE, old_role=NO_ROLE)

    admin_connection = self.make_v1_connection(config_broker, api, auth_provider)
    admin_user = admin_connection.users(admin_connection.user_id).fetch()
    connection.clients(client_id).invites().create(email=admin_user.email, role=ADMIN_ROLE, old_role=NO_ROLE)

    connection.create_experiment_as(client_id)
    other_connection.create_experiment_as(client_id)
    assert len(connection.clients(client_id).experiments().fetch().data) == 2
    assert len(other_connection.clients(client_id).experiments().fetch().data) == 2
    assert len(admin_connection.clients(client_id).experiments().fetch().data) == 2

    connection.clients(client_id).update(client_security={"allow_users_to_see_experiments_by_others": False})
    assert len(connection.clients(client_id).experiments().fetch().data) == 2
    assert len(other_connection.clients(client_id).experiments().fetch().data) == 1
    assert len(admin_connection.clients(client_id).experiments().fetch().data) == 2

  def test_experiment_list_paging(self, connection):
    e1, e2, e3 = (connection.create_any_experiment() for _ in range(3))

    def fetcher(*a, **kw):
      return connection.clients(connection.client_id).experiments().fetch(*a, **kw)

    paging = fetcher(limit=1)
    assert paging.count == 3
    assert id_from_paging_marker(paging.paging.before) == e3.id
    assert id_from_paging_marker(paging.paging.after) == e3.id
    assert len(paging.data) == 1
    assert paging.data[0].id == e3.id

    paging = fetcher(limit=2)
    assert paging.count == 3
    assert id_from_paging_marker(paging.paging.before) == e2.id
    assert id_from_paging_marker(paging.paging.after) == e3.id
    assert len(paging.data) == 2
    assert paging.data[0].id == e3.id
    assert paging.data[1].id == e2.id

    paging = fetcher(limit=1, after=paging_marker_from_id(e1.id))
    assert paging.count == 3
    assert id_from_paging_marker(paging.paging.before) == e2.id
    assert id_from_paging_marker(paging.paging.after) == e2.id
    assert len(paging.data) == 1
    assert paging.data[0].id == e2.id

    paging = fetcher(limit=2, after=paging_marker_from_id(e1.id))
    assert paging.count == 3
    assert id_from_paging_marker(paging.paging.before) == e2.id
    assert paging.paging.after is None
    assert len(paging.data) == 2
    assert paging.data[0].id == e3.id
    assert paging.data[1].id == e2.id

    paging = fetcher(limit=1, before=paging_marker_from_id(e3.id))
    assert paging.count == 3
    assert id_from_paging_marker(paging.paging.before) == e2.id
    assert id_from_paging_marker(paging.paging.after) == e2.id
    assert len(paging.data) == 1
    assert paging.data[0].id == e2.id

    paging = fetcher(limit=2, before=paging_marker_from_id(e3.id))

    assert paging.count == 3
    assert paging.paging.before is None
    assert id_from_paging_marker(paging.paging.after) == e2.id
    assert len(paging.data) == 2
    assert paging.data[0].id == e2.id
    assert paging.data[1].id == e1.id

  @pytest.mark.parametrize("prefix", ("", ","))
  def test_experiment_invalid_paging(self, connection, client_id, prefix):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().fetch(before=prefix + "abcde")
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().fetch(before=prefix + "1,2")
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().fetch(before=prefix + "abc,def", sort=EXPERIMENT_RECENCY)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().fetch(before=prefix + "1", sort=EXPERIMENT_RECENCY)

  def test_experiment_list_search(self, connection, client_id):
    e = connection.create_experiment(
      {
        "name": "string to search for",
        "parameters": [
          {"name": "a", "type": "int", "bounds": {"min": 1, "max": 50}},
        ],
      }
    )
    paging = connection.clients(client_id).experiments().fetch(search="search")
    assert paging.count == 1
    assert paging.paging.before is None
    assert id_from_paging_marker(paging.paging.after) == e.id
    assert len(paging.data) == 1
    assert [d.id for d in paging.data] == [e.id]

  # TODO: Speed up this test, can we avoid sleeps?
  @pytest.mark.slow
  def test_experiment_list_sort(self, connection, client_id):
    # NOTE: sorting by time so must have some delay
    # since minimum timestep is 1s for observations
    match = "floop"
    e1 = connection.create_any_experiment(name=match)
    sleep(1)
    e2 = connection.create_any_experiment(name="no match")
    sleep(1)
    e3 = connection.create_any_experiment(name=match)
    for e in (e3, e1):
      sleep(1)
      s = connection.experiments(e.id).suggestions().create()
      connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 1}])
    for page_size in (1, 2, 3, 100):
      # used only on the admin
      last_updated = (
        connection.clients(client_id)
        .experiments()
        .fetch(
          sort=EXPERIMENT_RECENCY,
          limit=page_size,
        )
        .iterate_pages()
      )
      assert [e.id for e in last_updated] == [e1.id, e3.id, e2.id]
      last_created = (
        connection.clients(client_id)
        .experiments()
        .fetch(
          sort="id",
          limit=page_size,
        )
        .iterate_pages()
      )
      assert [e.id for e in last_created] == [e3.id, e2.id, e1.id]
      search_by_recency = (
        connection.clients(client_id)
        .experiments()
        .fetch(
          search=match,
          sort=EXPERIMENT_RECENCY,
          limit=page_size,
        )
        .iterate_pages()
      )
      assert [e.id for e in search_by_recency] == [e1.id, e3.id]
      search_by_id = (
        connection.clients(client_id)
        .experiments()
        .fetch(
          search=match,
          sort="id",
          limit=page_size,
        )
        .iterate_pages()
      )
      assert [e.id for e in search_by_id] == [e3.id, e1.id]

  def test_experiment_list_period(self, connection, client_id, services):
    e1, e2, e3 = (connection.create_any_experiment() for _ in range(3))
    e1_date_created = current_datetime() - datetime.timedelta(seconds=4)
    e2_date_created = current_datetime()
    e3_date_created = current_datetime() + datetime.timedelta(seconds=4)

    update_tuples = [(e1, e1_date_created), (e2, e2_date_created), (e3, e3_date_created)]
    for update in update_tuples:
      services.database_service.update(
        services.database_service.query(Experiment).filter_by(id=update[0].id),
        {Experiment.date_created: update[1]},
      )

    e1 = connection.experiments(e1.id).fetch()
    e2 = connection.experiments(e2.id).fetch()
    e3 = connection.experiments(e3.id).fetch()

    experiments = connection.clients(client_id).experiments().fetch(period_end=e1.created)
    assert len(experiments.data) == 0

    experiments = connection.clients(client_id).experiments().fetch(period_start=e2.created)
    assert len(experiments.data) == 2
    experiment_ids = [e.id for e in experiments.data]
    assert e1.id not in experiment_ids
    assert e2.id in experiment_ids
    assert e3.id in experiment_ids

    experiments = connection.clients(client_id).experiments().fetch(period_end=e2.created + 1)
    assert len(experiments.data) == 2
    experiment_ids = [e.id for e in experiments.data]
    assert e1.id in experiment_ids
    assert e2.id in experiment_ids
    assert e3.id not in experiment_ids

    experiments = connection.clients(client_id).experiments().fetch(period_start=e2.created, period_end=e2.created + 1)
    assert len(experiments.data) == 1
    experiment_ids = [e.id for e in experiments.data]
    assert e1.id not in experiment_ids
    assert e2.id in experiment_ids
    assert e3.id not in experiment_ids

    experiments = connection.clients(client_id).experiments().fetch(period_start=e3.created + 1)
    assert len(experiments.data) == 0

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      experiments = connection.clients(client_id).experiments().fetch(period_start=1000, period_end=999)

  def test_experiment_list_paging_and_period(self, connection, client_id, services):
    e1, e2, e3 = (connection.create_any_experiment() for _ in range(3))
    e1_date_created = current_datetime() - datetime.timedelta(seconds=4)
    e2_date_created = current_datetime()
    e3_date_created = current_datetime() + datetime.timedelta(seconds=4)

    update_tuples = [(e1, e1_date_created), (e2, e2_date_created), (e3, e3_date_created)]
    for update in update_tuples:
      services.database_service.update(
        services.database_service.query(Experiment).filter_by(id=update[0].id),
        {Experiment.date_created: update[1]},
      )

    e1 = connection.experiments(e1.id).fetch()
    e2 = connection.experiments(e2.id).fetch()
    e3 = connection.experiments(e3.id).fetch()

    experiments = (
      connection.clients(client_id)
      .experiments()
      .fetch(
        period_start=e2.created,
        before=paging_marker_from_id(e3.id),
      )
    )
    assert len(experiments.data) == 1
    experiment_ids = [e.id for e in experiments.data]
    assert e1.id not in experiment_ids
    assert e2.id in experiment_ids
    assert e3.id not in experiment_ids

    experiments = (
      connection.clients(client_id)
      .experiments()
      .fetch(
        period_start=e2.created,
        before=paging_marker_from_id(e2.id),
      )
    )
    assert len(experiments.data) == 0

  @pytest.mark.slow
  def test_experiment_list_ascending(self, connection, client_id):
    paging_limit = 10
    e_first, *_, e_last = (connection.create_any_experiment() for _ in range(paging_limit + 1))
    sort_methods = ("id", "recent")
    for sort in sort_methods:

      def fetcher(*a, **kw):
        return connection.clients(connection.client_id).experiments().fetch(*a, **kw)

      paging = fetcher(limit=paging_limit, sort=sort)
      before = paging.paging.before
      assert len(paging.data) == paging_limit
      assert paging.data[0].id == e_last.id

      paging = fetcher(limit=paging_limit, sort=sort, before=before)
      assert len(paging.data) == 1
      assert paging.data[0].id == e_first.id

      paging = fetcher(limit=paging_limit, sort=sort, ascending=True)
      after = paging.paging.after
      assert len(paging.data) == paging_limit
      assert paging.data[0].id == e_first.id

      paging = fetcher(limit=paging_limit, sort=sort, ascending=True, after=after)
      assert len(paging.data) == 1
      assert paging.data[0].id == e_last.id
