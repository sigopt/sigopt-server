# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *

from integration.v1.endpoints.web_data.web_data_base import WebDataBase


class TestFetchWebData(WebDataBase):
  def test_fetch_one(self, connection, project, simple_run_view_args):
    new_view = connection.web_data().create(**simple_run_view_args)
    assert self.clean_server_response(new_view) == simple_run_view_args
    fetch_args = dict(
      parent_resource_type="project",
      web_data_type="run_view",
      parent_resource_id=dict(
        client=new_view.parent_resource_id["client"],
        project=new_view.parent_resource_id["project"],
      ),
    )
    fetched_views = connection.web_data().fetch(**fetch_args)
    assert fetched_views.data[0] == new_view
    assert fetched_views.count == 1

  def test_fetch_three(self, connection, project, simple_run_view_args):
    created_views = []
    for i in range(3):
      args = simple_run_view_args
      args["display_name"] = str(i)
      created_views.append(connection.web_data().create(**args))

    fetch_args = dict(
      parent_resource_type="project",
      web_data_type="run_view",
      parent_resource_id=dict(
        client=simple_run_view_args["parent_resource_id"]["client"],
        project=simple_run_view_args["parent_resource_id"]["project"],
      ),
    )
    fetched_views = connection.web_data().fetch(**fetch_args)

    created_views.reverse()
    assert fetched_views.data == created_views
    assert fetched_views.count == len(created_views)
