# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import math
from http import HTTPStatus

import pytest
from flaky import flaky
from sigopt.exception import ApiException

from integration.utils.wait import wait_for
from integration.v1.endpoints.importances.test_base import ExperimentImportancesTestBase


class TestExperimentMetricImportances(ExperimentImportancesTestBase):
  def endpoint(self, connection, experiment):
    return connection.experiments(experiment.id).metric_importances().fetch()

  def wait_for_importances(self, connection, experiment):
    def get_importances():
      try:
        return self.endpoint(connection, experiment).data
      except ApiException as ae:
        if ae.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
          return None
        raise

    return wait_for(get_importances, timeout_message="Metric importances were not computed before the timeout")

  @pytest.mark.slow
  @flaky(max_runs=2)
  def test_metric_importances_logic(
    self,
    connection,
    client_id,
    meta,
    wait_for_empty_optimization_queue,
  ):
    e = self.create_experiment_and_observations(connection, client_id, meta)
    # NOTE: the optimization messages caused by the previous line sometimes take longer than 10s to process
    wait_for_empty_optimization_queue(timeout=20)
    importances = self.endpoint(connection, e).data

    for metric_importances in importances:
      importance_map = metric_importances.importances
      assert importance_map["a"] > importance_map["g"]
      assert importance_map["b"] > importance_map["g"]

  @pytest.mark.slow
  def test_metric_importances_sum(
    self,
    connection,
    client_id,
    meta,
    wait_for_empty_optimization_queue,
  ):
    e = self.create_experiment_and_observations(connection, client_id, meta)
    wait_for_empty_optimization_queue(timeout=20)
    importances = self.wait_for_importances(connection, e)

    for metric_importances in importances:
      importance_map = metric_importances.importances
      assert not all(v is None for v in importance_map.values())
      assert math.isclose(sum(importance_map.values()), 1)

  def test_metric_importances_no_observations(self, connection, client_id):
    self.base_test_importances_no_observations(connection, client_id)

  def test_metric_importances_not_enough(self, connection, client_id):
    self.base_test_importances_not_enough(connection, client_id)

  @pytest.mark.slow
  def test_metric_importances_not_on_development(self, development_connection, client_id):
    self.base_test_importances_not_on_development(development_connection, client_id)
