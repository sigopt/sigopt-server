# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import re

import pytest

from zigopt.common.strings import random_string
from zigopt.project.model import MAX_ID_LENGTH as MAX_PROJECT_ID_LENGTH

from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest
from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META


class TestSummary(ExperimentBrowserTest):
  @pytest.fixture
  def project(self, api_connection, experiment):
    return (
      api_connection.clients(experiment.client)
      .projects()
      .create(
        id=random_string(MAX_PROJECT_ID_LENGTH).lower(),
        name=f"test project for {type(self).__name__}",
      )
    )

  @pytest.fixture
  def ai_experiment(self, api_connection, project):
    return (
      api_connection.clients(project.client).projects(project.id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)
    )

  def test_ai_experiment_redirect(self, logged_in_page, ai_experiment, routes):
    page = logged_in_page
    with page.expect_navigation(url=re.compile(f"^.*\\/aiexperiment\\/{ai_experiment.id}$")):
      page.goto(routes.get_full_url(f"/experiment/{ai_experiment.id}"))
    page.wait_for_selector(f'.title >> text="{ai_experiment.name}"')
