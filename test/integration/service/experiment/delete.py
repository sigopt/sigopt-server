# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.service.experiment.test_base import ExperimentServiceTestBase


class TestExperimentDelete(ExperimentServiceTestBase):
  def test_delete(self, services, experiment):
    services.experiment_service.insert(experiment)
    assert experiment.deleted is False
    services.experiment_service.delete(experiment)
    assert experiment.deleted is True

  def test_delete_persists(self, services, experiment):
    services.experiment_service.insert(experiment)
    services.experiment_service.delete(experiment)
    services.experiment_service.find_by_id(experiment.id)
    assert experiment.deleted is True

  def test_delete_without_insert(self, services, experiment):
    assert experiment.deleted is None
    services.experiment_service.delete(experiment)
    # Note: is this expected?
    assert experiment.deleted is None

  def test_delete_deleted(self, services, experiment):
    services.experiment_service.insert(experiment)
    services.experiment_service.delete(experiment)
    services.experiment_service.delete(experiment)
    assert experiment.deleted is True
    services.experiment_service.find_by_id(experiment.id)
    assert experiment.deleted is True

  def test_delete_by_id(self, services, experiment):
    services.experiment_service.insert(experiment)
    with pytest.raises(Exception):
      services.experiment_service.delete(experiment.id)
