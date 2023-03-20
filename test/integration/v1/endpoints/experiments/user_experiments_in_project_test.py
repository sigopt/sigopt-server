# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common.lists import find
from zigopt.common.strings import random_string
from zigopt.handlers.experiments.list_base import EXPERIMENT_RECENCY
from zigopt.project.model import MAX_ID_LENGTH as MAX_PROJECT_ID_LENGTH
from zigopt.project.model import Project

from integration.v1.test_base import V1Base


class TestUserExperimentsInProject(V1Base):
  def test_experiments(self, services, owner_connection):
    other_client = owner_connection.organizations(owner_connection.organization_id).clients().create(name="Hello")
    project1, project2 = (
      services.project_service.insert(
        Project(
          name=f"test project for users experiment list client {cid}",
          reference_id=random_string(MAX_PROJECT_ID_LENGTH).lower(),
          client_id=cid,
          created_by=None,
        )
      )
      for cid in (owner_connection.client_id, other_client.id)
    )

    first_experiment = owner_connection.create_any_experiment(
      client_id=owner_connection.client_id,
      project=project1.reference_id,
    )
    second_experiment = owner_connection.create_any_experiment(
      client_id=other_client.id,
      project=project2.reference_id,
    )
    third_experiment = owner_connection.create_any_experiment(
      client_id=other_client.id,
    )
    experiments = owner_connection.users(owner_connection.user_id).experiments().fetch(sort=EXPERIMENT_RECENCY).data
    e1 = find(experiments, lambda e: e.id == first_experiment.id)
    assert e1 is not None
    assert e1.project == project1.reference_id
    e2 = find(experiments, lambda e: e.id == second_experiment.id)
    assert e2 is not None
    assert e2.project == project2.reference_id
    e3 = find(experiments, lambda e: e.id == third_experiment.id)
    assert e3 is not None
    assert e3.project is None
