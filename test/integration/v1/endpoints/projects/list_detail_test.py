# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common.sigopt_datetime import current_datetime
from zigopt.common.strings import random_string
from zigopt.project.model import MAX_ID_LENGTH, Project
from zigopt.user.model import User

from integration.auth import AuthProvider
from integration.v1.test_base import V1Base


class TestProjectsListEndpoint(V1Base):
  def make_project(self, services, name, client_id, created_by=None, **kwargs):
    project = Project(
      name=name,
      client_id=client_id,
      reference_id=random_string(MAX_ID_LENGTH).lower(),
      created_by=created_by,
      date_created=current_datetime(),
      date_updated=current_datetime(),
      **kwargs,
    )
    return services.project_service.insert(project)

  def make_user(self, services, **kwargs):
    user = User(
      email=AuthProvider.randomly_generated_email(),
      **kwargs,
    )
    services.user_service.insert(user)
    return user

  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  @pytest.fixture
  def user1(self, services):
    return self.make_user(
      services,
      name="Project list test user 1",
    )

  @pytest.fixture
  def user2(self, services):
    return self.make_user(
      services,
      name="Project list test user 2",
    )

  @pytest.fixture
  def user1_projects(self, services, client_id, user1):
    return [
      self.make_project(
        services,
        name=f"user 1 test project {i}",
        client_id=client_id,
        created_by=user1.id,
      )
      for i in range(2)
    ]

  @pytest.fixture
  def user2_projects(self, services, client_id, user2):
    return [
      self.make_project(
        services,
        name=f"user 2 test project {i}",
        client_id=client_id,
        created_by=user2.id,
      )
      for i in range(2)
    ]

  @pytest.fixture
  def archived_projects(self, services, client_id, user1, user2):
    return [
      self.make_project(
        services,
        name="user 1 archived project",
        client_id=client_id,
        created_by=user1.id,
        deleted=True,
      ),
      self.make_project(
        services,
        name="user 2 archived project",
        client_id=client_id,
        created_by=user2.id,
        deleted=True,
      ),
    ]

  @pytest.fixture
  def no_user_projects(self, services, client_id, user1):
    return [self.make_project(services, name=f"no user test project {i}", client_id=client_id,) for i in range(2)] + [
      services.project_service.find_by_client_and_reference_id(client_id=client_id, reference_id="sigopt-examples")
    ]

  @pytest.fixture
  def other_client_projects(self, services, client_id, user1):
    assert str(client_id) != "1"
    return [
      self.make_project(
        services,
        name=f"other client test project {i}",
        client_id=1,
      )
      for i in range(2)
    ]

  @pytest.fixture
  def client_projects(self, user1_projects, user2_projects, no_user_projects, archived_projects):
    return [
      *user1_projects,
      *user2_projects,
      *no_user_projects,
    ]

  @pytest.fixture
  def all_test_projects(
    self, user1_projects, user2_projects, no_user_projects, other_client_projects, archived_projects
  ):
    return [
      *user1_projects,
      *user2_projects,
      *no_user_projects,
      *other_client_projects,
      *archived_projects,
    ]

  def check_projects_with_filter(self, connection, client_id, projects, **filters):
    first_page = connection.clients(client_id).projects().fetch(limit=2, **filters)
    assert len(first_page.data) == 2
    assert first_page.count == len(projects)
    fetched_projects = list(connection.clients(client_id).projects().fetch(limit=2, **filters).iterate_pages())
    assert all(p.client == str(client_id) for p in fetched_projects)
    assert len(fetched_projects) == len(projects)
    assert set(p.id for p in fetched_projects) == set(p.reference_id for p in projects)
    return fetched_projects

  def test_list(self, connection, client_id, client_projects, all_test_projects):
    self.check_projects_with_filter(connection, client_id, client_projects)

  def test_list_with_user_filter(self, connection, client_id, user1, user1_projects, all_test_projects):
    self.check_projects_with_filter(connection, client_id, user1_projects, user=user1.id)

  def test_list_with_dev_token(self, development_connection, client_id, client_projects, all_test_projects):
    self.check_projects_with_filter(development_connection, client_id, client_projects)

  @pytest.mark.parametrize(
    "sort_field,sort_key",
    [
      ("created", lambda p: (p.date_created, p.id)),
      ("updated", lambda p: (p.date_updated, p.id)),
    ],
  )
  @pytest.mark.parametrize("ascending", (True, False))
  def test_list_sort(self, sort_field, sort_key, ascending, connection, client_id, client_projects):
    # NOTE: the python client doesn't pick up on ascending,
    # but it does understand after/before
    paging_kwargs = {}
    if ascending:
      paging_kwargs["after"] = None
    fetched_projects = list(
      connection.clients(client_id)
      .projects()
      .fetch(limit=2, ascending=ascending, sort=sort_field, **paging_kwargs)
      .iterate_pages()
    )
    assert len(fetched_projects) == len(client_projects)
    sorted_test_projects = sorted(client_projects, key=sort_key)
    if not ascending:
      sorted_test_projects = list(reversed(sorted_test_projects))
    assert [p.id for p in fetched_projects] == [p.reference_id for p in sorted_test_projects]

  def test_list_archived(self, connection, client_id, client_projects, archived_projects):
    plain_ids = {p.reference_id for p in client_projects}
    archived_ids = {p.reference_id for p in archived_projects}
    all_ids = plain_ids | archived_ids
    plain_list = {p.id for p in connection.clients(client_id).projects().fetch().iterate_pages()}
    assert plain_list == plain_ids
    archived_list = {p.id for p in connection.clients(client_id).projects().fetch(deleted=True).iterate_pages()}
    assert archived_list == all_ids
