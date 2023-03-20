# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy
from http import HTTPStatus
from time import sleep

from integration.base import RaisesApiException
from integration.v1.endpoints.web_data.web_data_base import WebDataBase


class TestUpdateWebData(WebDataBase):
  def test_update_one_view(self, connection, project, simple_run_view_args):
    original_view = connection.web_data().create(**simple_run_view_args)
    update_args = deepcopy(simple_run_view_args)
    update_args["id"] = original_view.id
    update_args["payload"]["column_state"] = simple_run_view_args["payload"]["column_state"] + "difrnt"
    sleep(1)
    updated_view = connection.web_data().update(**update_args)

    assert updated_view.payload["column_state"] == update_args["payload"]["column_state"]
    assert updated_view.updated > original_view.updated
    assert original_view.created_by == updated_view.created_by
    assert original_view.created == updated_view.created

  def test_cant_move_projects(self, connection, project, project2, simple_run_view_args):
    original_view = connection.web_data().create(**simple_run_view_args)
    update_args = deepcopy(simple_run_view_args)
    update_args["id"] = original_view.id
    update_args["payload"]["column_state"] = simple_run_view_args["payload"]["column_state"] + "difrnt"
    update_args["parent_resource_id"]["project"] = project2.id

    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.web_data().update(**update_args)

    del update_args["id"]
    connection.web_data().create(**update_args)

  def test_update_permissions(self, connection, random_connection, project, simple_run_view_args):
    original_view = connection.web_data().create(**simple_run_view_args)
    update_args = deepcopy(simple_run_view_args)
    update_args["id"] = original_view.id
    update_args["payload"]["column_state"] = simple_run_view_args["payload"]["column_state"] + "difrnt"

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      random_connection.web_data().update(**update_args)

    connection.web_data().update(**update_args)
