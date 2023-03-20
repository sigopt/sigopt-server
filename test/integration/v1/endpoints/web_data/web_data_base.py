# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common import *

from integration.v1.test_base import V1Base


class WebDataBase(V1Base):
  @pytest.fixture
  def project(self, connection):
    project_id = "views-project"
    project_name = "views project"
    return (
      connection.clients(connection.client_id)
      .projects()
      .create(
        id=project_id,
        name=project_name,
      )
    )

  @pytest.fixture
  def project2(self, connection):
    project_id = "views-project2"
    project_name = "views project2"
    return (
      connection.clients(connection.client_id)
      .projects()
      .create(
        id=project_id,
        name=project_name,
      )
    )

  @pytest.fixture
  def random_connection(self, config_broker, api, auth_provider):
    return self.make_v1_connection(config_broker, api, auth_provider)

  @pytest.fixture
  def simple_run_view_args(self, project):
    return dict(
      web_data_type="run_view",
      parent_resource_type="project",
      parent_resource_id={"project": project.id, "client": project.client},
      display_name="testview123",
      payload={"filters": [], "sort": [], "column_state": "this is an arbitrary string"},
    )

  def clean_server_response(self, server_response):
    server_response_cleaned = recursively_omit_keys(server_response.to_json(), ["object"])
    del server_response_cleaned["updated"]
    del server_response_cleaned["created"]
    del server_response_cleaned["created_by"]
    del server_response_cleaned["id"]
    return server_response_cleaned

  def nested_set(self, dic, keys, value):
    for key in keys[:-1]:
      dic = dic.setdefault(key, {})
    dic[keys[-1]] = value
