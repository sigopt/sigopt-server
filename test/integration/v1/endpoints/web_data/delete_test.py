# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy
from http import HTTPStatus

import pytest

from zigopt.common import *

from integration.base import RaisesApiException
from integration.v1.endpoints.web_data.web_data_base import WebDataBase


def create_to_delete_args(create_args, _id):
  delete_args = deepcopy(create_args)
  del delete_args["payload"]
  del delete_args["parent_resource_id"]
  delete_args["parent_resource_id"] = dict(
    project=create_args["parent_resource_id"]["project"],
    client=create_args["parent_resource_id"]["client"],
  )
  delete_args["id"] = _id
  return delete_args


class TestDeleteWebData(WebDataBase):
  def test_delete_a_view(self, connection, simple_run_view_args, project):
    created_views = []
    for i in range(3):
      args = simple_run_view_args
      args["display_name"] = str(i)
      created_views.append(connection.web_data().create(**args))

    view_to_delete = created_views[1]
    delete_args = create_to_delete_args(simple_run_view_args, view_to_delete.id)

    connection.web_data().delete(**delete_args)

    fetch_args = deepcopy(delete_args)
    del fetch_args["id"]

    fetched_after = connection.web_data().fetch(**fetch_args)
    expected_views = [created_views[2], created_views[0]]
    assert fetched_after.data == expected_views

  def test_delete_permissions(self, connection, random_connection, simple_run_view_args, project):
    created_view = connection.web_data().create(**simple_run_view_args)

    delete_args = create_to_delete_args(simple_run_view_args, created_view.id)

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      random_connection.web_data().delete(**delete_args)

    connection.web_data().delete(**delete_args)

  @pytest.mark.parametrize(
    "keys,value",
    [
      [["id"], "saskatchewan"],
      [["id"], -3],
      [["parent_resource_id", "project"], 5],
      [["parent_resource_id", "client"], "albatross"],
      [["parent_resource_type"], "something we will likely never support"],
      [["web_data_type"], "also something we will likely never support"],
    ],
  )
  def test_delete_incorrect_args(self, connection, random_connection, simple_run_view_args, project, keys, value):
    created_view = connection.web_data().create(**simple_run_view_args)

    delete_args = create_to_delete_args(simple_run_view_args, created_view.id)

    bad_delete_args = deepcopy(delete_args)
    self.nested_set(bad_delete_args, keys, value)
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.BAD_REQUEST):
      connection.web_data().delete(**bad_delete_args)

    connection.web_data().delete(**delete_args)

  def test_delete_wrong_project(self, connection, project, project2, simple_run_view_args):
    args1 = deepcopy(simple_run_view_args)
    args1["parent_resource_id"]["project"] = project.id
    created_view1 = connection.web_data().create(**args1)

    args2 = deepcopy(simple_run_view_args)
    args2["parent_resource_id"]["project"] = project2.id
    created_view2 = connection.web_data().create(**args2)

    bad_delete_args = create_to_delete_args(args1, created_view2.id)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.web_data().delete(**bad_delete_args)

    ok_delete_args = create_to_delete_args(args1, created_view1.id)
    connection.web_data().delete(**ok_delete_args)
