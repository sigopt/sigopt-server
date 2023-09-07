# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy
from http import HTTPStatus

import pytest

from zigopt.common import *

from integration.base import RaisesApiException
from integration.v1.endpoints.web_data.web_data_base import WebDataBase


class TestCreateWebData(WebDataBase):
  def test_create_simple_view(self, connection, simple_run_view_args, project):
    new_view = connection.web_data().create(**simple_run_view_args)
    assert self.clean_server_response(new_view) == simple_run_view_args

  def test_ag_run_view(self, connection, simple_run_view_args, project):
    ag_args = deepcopy(simple_run_view_args)
    ag_args["web_data_type"] = "ag_run_view"
    ag_args["payload"] = {
      "columnState": [
        {
          "colId": "f",
          "hide": False,
          "aggFunc": None,
          "width": 1,
          "pivotIndex": None,
          "pinned": None,
          "rowGroupIndex": None,
        },
      ],
      "columnGroupState": [{"groupId": "2", "open": False}],
      "sortModel": [{"colId": "values.AUPRC.value", "sort": "desc"}],
      "filterModel": {},
    }
    new_view = connection.web_data().create(**ag_args)
    assert self.clean_server_response(new_view) == ag_args

  def test_create_non_existant(self, connection, simple_run_view_args, project):
    bad_args = deepcopy(simple_run_view_args)
    bad_args["web_data_type"] = "ran_view"
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      error = connection.web_data().create(**bad_args)
      assert "ran_view" in error

  def test_create_complex_view(self, connection, project):
    create_args = dict(
      web_data_type="run_view",
      parent_resource_type="project",
      parent_resource_id={"project": project.id, "client": project.client},
      display_name="testing-filter",
      payload=dict(
        column_state="this is an arbitrary alliterated string",
        filters=[
          {"operator": "==", "field": "carrots", "value": 23, "enabled": False},
          {"operator": ">=", "field": "cucumber", "value": "yes", "enabled": True},
        ],
        sort=[{"key": "carrots", "ascending": True}],
      ),
    )
    new_view = connection.web_data().create(**create_args)
    assert self.clean_server_response(new_view) == create_args

  def test_create_permissions(self, services, connection, random_connection, project, simple_run_view_args):
    connection.web_data().create(**simple_run_view_args)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      simple_run_view_args["display_name"] = simple_run_view_args["display_name"] + "uniqueify"
      random_connection.web_data().create(**simple_run_view_args)

  def test_can_create_duplicate_names(self, services, connection, project, simple_run_view_args):
    connection.web_data().create(**simple_run_view_args)
    connection.web_data().create(**simple_run_view_args)

  # TODO: This is fragile/slow - move web data limits to config broker(?)
  # this is hardcoded in src/python/zigopt/handlers/web_data/base.py atm.
  def test_create_limits(self, services, connection, project, simple_run_view_args):
    for i in range(100):
      simple_run_view_args["display_name"] = str(i)
      connection.web_data().create(**simple_run_view_args)

    with RaisesApiException(HTTPStatus.FORBIDDEN):
      error = connection.web_data().create(**simple_run_view_args)
      assert simple_run_view_args["display_name"] in error

  @pytest.mark.parametrize(
    "keys,value",
    [
      [["id"], "saskatchewan"],
      [["id"], -3],
      [["parent_resource_id", "project"], 5],
      [["parent_resource_id", "client"], "albatross"],
      [["parent_resource_type"], "something we will likely never support"],
      [["web_data_type"], "also something we will likely never support"],
      [["payload", "sort"], "string"],
      [["payload", "view", "sort"], "string"],
      [["payload", "view", "filters"], [{"operator": "==", "field": "c", "value": 23, "enabled": False, "x": "s"}]],
      [["payload", "view", "filters"], [{"operator": "==", "field": "c", "value": [23], "enabled": False}]],
      [["payload", "view", "filters"], [{"operator": "invalid", "field": "c", "value": 23, "enabled": False}]],
      [["payload", "view", "filters"], [{"operator": "==", "value": 23, "enabled": True}]],
      [["payload", "view", "filters"], [{"operator": "invalid", "field": 33, "enabled": False}]],
      [["payload", "display_name"], 33],
      [["payload", "view", "sort"], [{"key": 33, "ascending": True}]],
    ],
  )
  def test_create_invalid_args(self, services, connection, project, simple_run_view_args, keys, value):
    bad_create_args = deepcopy(simple_run_view_args)
    self.nested_set(bad_create_args, keys, value)

    with RaisesApiException(HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND):
      connection.web_data().create(**bad_create_args)
