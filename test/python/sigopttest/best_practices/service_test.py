# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.best_practices.constants import *
from zigopt.best_practices.service import BestPracticesService
from zigopt.experiment.model import Experiment
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *


class TestBestPracticesService(object):
  @pytest.fixture(scope="session")
  def best_practices_service(self):
    services = Mock()
    return BestPracticesService(services)

  def assert_not_best_practices_violations(self, best_practices_service, experiment):
    for warnings in (
      best_practices_service.check_max_observations(experiment, 0),
      best_practices_service.check_max_open_suggestions(experiment, 0),
      best_practices_service.check_parallel_bandwidth(experiment),
      best_practices_service.check_max_constraints(experiment),
      best_practices_service.check_observation_budget(experiment),
      best_practices_service.check_max_dimension(experiment),
    ):
      pytest.raises(StopIteration, next, warnings)

  def test_default_experiment(self, best_practices_service):
    meta = ExperimentMeta()
    experiment = Experiment(experiment_meta=meta)
    self.assert_not_best_practices_violations(best_practices_service, experiment)

  def test_experiment_with_constraints(self, best_practices_service):
    all_parameters_unsorted = []
    dim = 10
    for i in range(dim):
      all_parameters_unsorted.append(
        ExperimentParameter(
          name=f"p{i}",
          bounds=Bounds(minimum=0, maximum=1),
          param_type=PARAMETER_DOUBLE,
        ),
      )
    constraint = ExperimentConstraint(
      type="less_than",
      terms=[Term(name=f"p{i}", coeff=1) for i in range(dim)],
      rhs=1,
    )

    constraints = [constraint for _ in range(MAX_LINEAR_CONSTRAINTS)]
    experiment_meta = ExperimentMeta(all_parameters_unsorted=all_parameters_unsorted, constraints=constraints)
    experiment = Experiment(experiment_meta=experiment_meta)
    self.assert_not_best_practices_violations(best_practices_service, experiment)

  def test_experiment_with_conditionals(self, best_practices_service):
    meta = ExperimentMeta()
    c = meta.conditionals.add()
    for _ in range(MAX_CONDITIONALS_BREADTH):
      c.values.add()
    meta.all_parameters_unsorted.add()

    experiment = Experiment(experiment_meta=meta)
    self.assert_not_best_practices_violations(best_practices_service, experiment)
