# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.experiment.model import Experiment
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *

from integration.service.suggestion.broker.test_base import SuggestionBrokerTestBase


# TODO(SN-1134): this can be a unit test
class TestShouldUseRandomForLowDiscrepancy(SuggestionBrokerTestBase):
  @pytest.mark.parametrize("parameters", [[ExperimentParameter() for _ in range(i)] for i in [1, 19, 20, 100]])
  @pytest.mark.parametrize(
    "conditionals", [[], [ExperimentConditional()], [ExperimentConditional(), ExperimentConditional()]]
  )
  def test_should_use_random_for_low_discrepancy_spe(self, services, parameters, conditionals):
    experiment = Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=parameters,
        conditionals=conditionals,
        observation_budget=60,
        development=False,
      ),
    )

    should_use_random = services.suggestion_broker.should_use_random_for_low_discrepancy(experiment)
    should_use_spe = services.optimizer.should_use_spe(
      experiment=experiment,
      num_observations=0,
    )
    assert should_use_random is should_use_spe

  @pytest.mark.parametrize(
    "priors",
    [
      Prior(prior_type=Prior.NORMAL, normal_prior=NormalPrior(mean=1, scale=1)),
      Prior(prior_type=Prior.BETA, beta_prior=BetaPrior(shape_a=1, shape_b=1)),
      Prior(prior_type=Prior.LAPLACE, laplace_prior=LaplacePrior(mean=1, scale=1)),
    ],
  )
  def test_should_use_random_for_low_discrepancy_priors(self, services, priors):
    parameters = []
    parameters.append(
      ExperimentParameter(
        name="p1",
        bounds=Bounds(minimum=0, maximum=1),
        param_type=PARAMETER_DOUBLE,
        prior=priors,
      )
    )
    experiment = Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=parameters,
        observation_budget=60,
        development=False,
      ),
    )
    should_use_random = services.suggestion_broker.should_use_random_for_low_discrepancy(experiment)
    assert should_use_random is True

  def test_should_use_random_for_low_discrepancy_constraints(self, services):
    parameters = []
    d = 5
    for i in range(d):
      parameters.append(
        ExperimentParameter(
          name=f"p{i}",
          bounds=Bounds(minimum=0, maximum=1),
          param_type=PARAMETER_DOUBLE,
        )
      )
    constraints = [
      ExperimentConstraint(
        type="less_than",
        terms=[Term(name=f"p{i}", coeff=1) for i in range(d)],
        rhs=1,
      ),
    ]
    experiment = Experiment(
      client_id=1,
      name="test experiment",
      experiment_meta=ExperimentMeta(
        all_parameters_unsorted=parameters,
        observation_budget=60,
        constraints=constraints,
        development=False,
      ),
    )
    should_use_random = services.suggestion_broker.should_use_random_for_low_discrepancy(experiment)
    assert should_use_random is True
