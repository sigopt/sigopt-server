# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common.sigopt_datetime import current_datetime
from zigopt.experiment.model import Experiment
from zigopt.optimization_aux.model import ExperimentOptimizationAux

from integration.service.test_base import ServiceBase


class TestExperimentOptimizationAux(ServiceBase):
  SOURCE_NAME = "fake source"

  @pytest.fixture
  def experiment(self, services):
    experiment = Experiment()
    services.experiment_service.insert(experiment)
    return experiment

  def experiment_optimization_aux(self, experiment, date_updated=None):
    aux = ExperimentOptimizationAux(
      experiment_id=experiment.id,
      source_name=self.SOURCE_NAME,
    )
    if date_updated is not None:
      aux.date_updated = date_updated
    return aux

  def test_insert_gets_defaults(self, services, experiment):
    experiment_optimization_aux = self.experiment_optimization_aux(experiment)
    services.database_service.insert(experiment_optimization_aux)

    (aux,) = services.aux_service.get_stored_auxes(experiment, self.SOURCE_NAME)
    assert aux.date_updated is None

  def test_insert_override_defaults(self, services, experiment):
    date_updated = current_datetime()
    experiment_optimization_aux = self.experiment_optimization_aux(experiment, date_updated)
    services.database_service.insert(experiment_optimization_aux)

    (aux,) = services.aux_service.get_stored_auxes(experiment, self.SOURCE_NAME)
    assert aux.date_updated == date_updated

  def test_upsert_gets_defaults(self, services, experiment):
    experiment_optimization_aux = self.experiment_optimization_aux(experiment)
    services.database_service.upsert(experiment_optimization_aux)

    (aux,) = services.aux_service.get_stored_auxes(experiment, self.SOURCE_NAME)
    assert aux.date_updated is None

  def test_upsert_overrides_defaults(self, services, experiment):
    date_updated = current_datetime()
    experiment_optimization_aux = self.experiment_optimization_aux(experiment, date_updated)
    services.database_service.upsert(experiment_optimization_aux)

    (aux,) = services.aux_service.get_stored_auxes(experiment, self.SOURCE_NAME)
    assert aux.date_updated == date_updated
