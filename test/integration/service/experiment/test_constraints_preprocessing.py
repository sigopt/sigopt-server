# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.experiment.model import Experiment
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.sigoptcompute.adapter import SCAdapter

from integration.service.experiment.test_base import ExperimentServiceTestBase


class TestHitAndRunFlag(ExperimentServiceTestBase):
  def _test_hitandrun_set_at_experiment_create(self, experiment, flag_state):
    assert experiment.force_hitandrun_sampling is flag_state

  def _test_hitandrun_set_in_sc_adapter_domain_info(self, experiment, flag_state):
    domain_info = SCAdapter.generate_domain_info(experiment)
    assert domain_info.force_hitandrun_sampling is flag_state

  def _test_hitandrun_flag_base(self, services, dim, flag_state):
    all_parameters_unsorted = []
    for i in range(dim):
      all_parameters_unsorted.append(
        ExperimentParameter(
          name=f"p{i}",
          bounds=Bounds(minimum=0, maximum=1),
          param_type=PARAMETER_DOUBLE,
        ),
      )
    constraints = [
      ExperimentConstraint(
        type="less_than",
        terms=[Term(name=f"p{i}", coeff=1) for i in range(dim)],
        rhs=1,
      ),
    ]
    experiment_meta = ExperimentMeta(all_parameters_unsorted=all_parameters_unsorted, constraints=constraints)
    experiment = Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=experiment_meta,
    )
    services.experiment_service.set_hitandrun_flag_using_rejection_sampling(experiment)
    services.experiment_service.insert(experiment)
    fetched_experiment = services.experiment_service.find_by_id(experiment.id)
    self._test_hitandrun_set_at_experiment_create(experiment, flag_state)
    self._test_hitandrun_set_at_experiment_create(fetched_experiment, flag_state)
    self._test_hitandrun_set_in_sc_adapter_domain_info(experiment, flag_state)
    self._test_hitandrun_set_in_sc_adapter_domain_info(fetched_experiment, flag_state)

  def test_hitandrun_is_false_for_easy_constraints(self, services):
    dim = 2
    hitandrun_flag_state = False
    self._test_hitandrun_flag_base(services, dim, hitandrun_flag_state)

  def test_hitandrun_is_true_for_difficult_constraints(self, services):
    dim = 10
    hitandrun_flag_state = True
    self._test_hitandrun_flag_base(services, dim, hitandrun_flag_state)
