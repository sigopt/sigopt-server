# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import re

import pytest
from requests import HTTPError

from zigopt.common import *

from integration.utils.make_values import make_values
from integration.web.experiment.test_base import ExperimentWebBase


class TestCopy(ExperimentWebBase):
  def copy_experiment(self, old_id, api_connection, logged_in_web_connection, include_observations):
    params = {"include_observations": "on"} if include_observations else {}
    response = logged_in_web_connection.post(f"/experiment/{old_id}/copy", params, allow_redirects=False)
    new_id = re.search("experiment/([0-9]*)", response.redirect_url).group(1)
    assert str(new_id) != str(old_id)
    return api_connection.experiments(new_id).fetch()

  def test_copy(self, api_connection, logged_in_web_connection, meta):
    with api_connection.create_experiment(meta) as e:
      e2 = self.copy_experiment(e.id, api_connection, logged_in_web_connection, include_observations=True)
      assert e2.name == e.name + " Copy"
      assert e2.type == e.type
      assert e2.parameters == e.parameters
      assert e2.created >= e.created
      assert e2.metadata == e.metadata
      assert e2.project == e.project

  def test_copy_project(self, api_connection, logged_in_web_connection):
    project = (
      api_connection.clients(api_connection.client_id).projects().create(id="other-project", name="Other project")
    )
    with api_connection.create_any_experiment(project=project.id) as e:
      e2 = self.copy_experiment(e.id, api_connection, logged_in_web_connection, include_observations=True)
      assert e2.project == e.project

  def test_copy_new_client(self, api_connection, logged_in_web_connection):
    new_client = api_connection.clients().create(name="Other client")
    project = api_connection.clients(new_client.id).projects().create(id="other-project", name="Other project")
    with api_connection.create_any_experiment(client_id=new_client.id, project=project.id) as e:
      assert e.client == new_client.id
      e2 = self.copy_experiment(e.id, api_connection, logged_in_web_connection, include_observations=True)
      assert e2.client == api_connection.client_id
      assert e2.project is None

  def test_copy_long_name(self, api_connection, logged_in_web_connection):
    with api_connection.create_any_experiment(name="01234567890123456789012345678901234567890123456789") as e:
      e2 = self.copy_experiment(e.id, api_connection, logged_in_web_connection, include_observations=True)
      assert e2.name == "012345678901234567890123456789012345678901... Copy"

  def test_copy_do_not_include_observations(self, api_connection, logged_in_web_connection, meta):
    with api_connection.create_experiment(meta) as e:
      s = api_connection.experiments(e.id).suggestions().create()
      api_connection.experiments(e.id).observations().create(suggestion=s.id, values=make_values(e), no_optimize=True)
      e2 = self.copy_experiment(e.id, api_connection, logged_in_web_connection, include_observations=False)
      assert api_connection.experiments(e.id).observations().fetch().count == 1
      assert e2.progress.observation_count == 0
      assert api_connection.experiments(e.id).suggestions().fetch().count == 1
      assert api_connection.experiments(e2.id).suggestions().fetch().count == 0

  def test_copy_include_observations(self, api_connection, logged_in_web_connection, meta):
    if meta.get("conditionals"):
      pytest.skip()
    with api_connection.create_experiment(meta) as e:
      s1 = api_connection.experiments(e.id).suggestions().create()
      s2 = api_connection.experiments(e.id).suggestions().create()
      o1 = (
        api_connection.experiments(e.id)
        .observations()
        .create(
          suggestion=s1.id,
          values=make_values(e),
          no_optimize=True,
        )
      )
      o2 = (
        api_connection.experiments(e.id)
        .observations()
        .create(
          suggestion=s2.id,
          values=make_values(e),
          no_optimize=True,
        )
      )
      try:
        e2 = self.copy_experiment(e.id, api_connection, logged_in_web_connection, include_observations=True)
      except HTTPError as e:
        raise Exception(
          f"Encountered an issue copying the experiment: {e}\n"
          f"HTTPError content: {e.response.content}\n"
          f"Observation 1: {o1}\n"
          f"Observation 2: {o2}"
        ) from e
      assert e2.progress.observation_count == 2
      assert e2.progress.observation_budget_consumed == (o1.task.cost + o2.task.cost if e2.tasks else 2.0)
      assert api_connection.experiments(e.id).suggestions().fetch().count == 2
      assert api_connection.experiments(e2.id).suggestions().fetch().count == 0
      assert e2.progress.last_observation.assignments == o2.assignments
      assert e2.progress.last_observation.value == o2.value
      assert e2.progress.first_observation.assignments == o1.assignments
      assert e2.progress.first_observation.value == o1.value

  def test_copy_large_experiment(self, api_connection, logged_in_web_connection, config_broker):
    observation_count = config_broker["features.maxObservationsCreateCount"] + 1
    with api_connection.create_any_experiment() as e:
      s = api_connection.experiments(e.id).suggestions().create()
      observations = [{"assignments": s.assignments, "values": make_values(e)} for _ in range(observation_count)]
      for batch in (observations[: len(observations) // 2], observations[len(observations) // 2 :]):
        api_connection.experiments(e.id).observations().create_batch(observations=batch, no_optimize=True)
      e2 = self.copy_experiment(e.id, api_connection, logged_in_web_connection, include_observations=True)
      assert e2.progress.observation_count == observation_count

  def test_copy_deleted(self, api_connection, logged_in_web_connection):
    e = api_connection.create_any_experiment()
    api_connection.experiments(e.id).delete()
    e2 = self.copy_experiment(e.id, api_connection, logged_in_web_connection, include_observations=True)
    assert e2.state != "deleted"
