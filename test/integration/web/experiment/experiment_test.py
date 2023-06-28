# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

from requests import HTTPError

from zigopt.common import *

from integration.base import RaisesHttpError
from integration.utils.make_values import make_values
from integration.web.experiment.test_base import ExperimentWebBase


class TestExperiment(ExperimentWebBase):
  def test_properties(self, api_connection, logged_in_web_connection):
    e = api_connection.create_any_experiment()
    user = api_connection.sessions().fetch().user
    assert user.name in logged_in_web_connection.get(f"/experiment/{e.id}/properties")

  def test_reset(self, api_connection, logged_in_web_connection):
    e = api_connection.create_any_experiment()
    s = api_connection.experiments(e.id).suggestions().create()
    api_connection.experiments(e.id).observations().create(suggestion=s.id, values=make_values(e), no_optimize=True)
    assert api_connection.experiments(e.id).fetch().progress.observation_count == 1
    logged_in_web_connection.post(f"/experiment/{e.id}/reset")
    assert api_connection.experiments(e.id).fetch().progress.observation_count == 0

  def test_experiment_does_not_exist(self, web_connection, logged_in_web_connection):
    route = "/experiment/1234567890"
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      logged_in_web_connection.get(route)
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get(route)

  def test_experiment_logged_out(self, web_connection, logged_in_web_connection, experiment_url):
    try:
      logged_in_web_connection.get(experiment_url)
    except HTTPError as e:
      if "aiexperiment" in e.response.text:
        pass
    with RaisesHttpError(HTTPStatus.NOT_FOUND):
      web_connection.get(experiment_url)
