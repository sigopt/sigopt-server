# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy

import pytest

from zigopt.common.strings import random_string
from zigopt.project.model import MAX_ID_LENGTH as MAX_PROJECT_ID_LENGTH

from integration.v1.constants import ALL_META
from integration.v1.test_base import V1Base


def prepare_experiment_meta(request):
  meta = ALL_META[request.param]
  return copy.deepcopy(meta)


class ExperimentsTestBase(V1Base):
  @pytest.fixture(
    params=[
      "conditionals",
      "constraints",
      "default",
      "multimetric",
      "multisolution",
      "search",
    ]
  )
  def any_meta(self, request, connection):
    return prepare_experiment_meta(request)

  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  @pytest.fixture
  def project(self, connection):
    return (
      connection.clients(connection.client_id)
      .projects()
      .create(
        id=random_string(MAX_PROJECT_ID_LENGTH).lower(),
        name=f"test project for {type(self).__name__}",
      )
    )


class ExperimentFeaturesTestBase(ExperimentsTestBase):
  @pytest.fixture
  def meta(self):
    raise NotImplementedError()

  def test_experiment_create_large_dimension(self, connection, client_id, meta):
    max_dimension = 50
    meta["observation_budget"] = max_dimension * 10
    meta["parameters"].extend(
      [
        dict(
          type="double",
          bounds=dict(min=0, max=1),
          name=f"x{i}",
        )
        for i in range(max_dimension - len(meta["parameters"]))
      ]
    )
    assert len(meta["parameters"]) == 50
    e = connection.clients(client_id).experiments().create(**meta)
    assert max_dimension == len(e.parameters)


class AiExperimentsTestBase(V1Base):
  @pytest.fixture(
    params=[
      "conditionals",
      "constraints",
      "default",
      "multimetric",
      "multisolution",
      "search",
    ]
  )
  def any_meta(self, request, connection):
    meta = prepare_experiment_meta(request)
    budget = meta.pop("observation_budget", None)
    if budget is not None:
      meta["budget"] = budget
    return meta

  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  @pytest.fixture
  def project(self, connection):
    return (
      connection.clients(connection.client_id)
      .projects()
      .create(
        id=random_string(MAX_PROJECT_ID_LENGTH).lower(),
        name=f"test project for {type(self).__name__}",
      )
    )
