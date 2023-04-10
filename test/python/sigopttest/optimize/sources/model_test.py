# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.optimization_aux.model import ExperimentOptimizationAux


class TestExperimentOptimizationAux:
  def test_default_values(self):
    experiment_optimization_aux = ExperimentOptimizationAux()
    assert experiment_optimization_aux.date_updated is None
