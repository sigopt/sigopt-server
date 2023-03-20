# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.client.model import Client
from zigopt.experiment.model import Experiment
from zigopt.organization.model import Organization

from integration.service.test_base import ServiceBase


class DatabaseServiceBase(ServiceBase):
  INITIAL_EXPERIMENT_NAME = "initial name"

  @pytest.fixture
  def database_service(self, services):
    return services.database_service

  @pytest.fixture
  def experiment_service(self, services):
    return services.experiment_service

  @pytest.fixture
  def organization(self, services):
    organization = Organization()
    services.organization_service.insert(organization)
    return organization

  @pytest.fixture
  def client(self, services, organization):
    client = Client(organization.id)
    services.client_service.insert(client)
    return client

  @pytest.fixture
  def experiment(self, services, client):
    experiment = Experiment(name=self.INITIAL_EXPERIMENT_NAME, client_id=client.id)
    services.experiment_service.insert(experiment)
    return experiment
