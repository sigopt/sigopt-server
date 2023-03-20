# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common import *

from integration.v1.constants import ALL_META
from integration.web.test_base import Routes, WebBase


class ExperimentWebBase(WebBase):
  @pytest.fixture(
    params=[
      "conditionals",
      "constraints",
      "default",
      "multimetric",
      "multisolution",
      "multitask",
    ]
  )
  def meta(self, request, api_connection):
    experiment_meta = ALL_META[request.param]
    return experiment_meta

  @pytest.fixture
  def project(self, api_connection):
    return api_connection.clients(api_connection.client_id).projects().create(name="test project", id="test-project")

  @pytest.fixture
  def experiment(self, api_connection, project):
    return api_connection.create_any_experiment(runs_only=True, project=project.id)

  @pytest.fixture(
    params=[
      p for p in Routes.APP_ROUTES if p.startswith("/experiment/") and ":observationId" not in p or p == "/experiments"
    ]
  )
  def experiment_url(self, request, experiment):
    replaced_url = request.param.replace(":experimentId", experiment.id)
    return replaced_url
