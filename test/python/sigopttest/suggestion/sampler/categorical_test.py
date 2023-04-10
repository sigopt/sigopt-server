# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.experiment.model import Experiment
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import PARAMETER_CATEGORICAL, ExperimentMeta
from zigopt.suggestion.sampler.categorical import CategoricalOnlySampler

from sigopttest.base.utils import partial_opt_args


class TestCategoricalOnlySampler:
  @pytest.fixture
  def experiment(self):
    meta = ExperimentMeta()
    p = meta.all_parameters_unsorted.add(name="p0", param_type=PARAMETER_CATEGORICAL)
    p.all_categorical_values.add(name="a", enum_index=1)
    p.all_categorical_values.add(name="b", enum_index=2)

    p = meta.all_parameters_unsorted.add(name="p1", param_type=PARAMETER_CATEGORICAL)
    p.all_categorical_values.add(name="c", enum_index=1)
    p.all_categorical_values.add(name="d", enum_index=2)

    c = meta.conditionals.add(name="c0")
    c.values.add(name="v0", enum_index=1)
    c.values.add(name="v1", enum_index=2)

    return Experiment(experiment_meta=meta)

  @pytest.fixture
  def services(self):
    return Mock()

  def test_categorical_only_sampler(self, experiment, services):
    sampler = CategoricalOnlySampler(services, experiment, partial_opt_args())
    (unprocessed_suggestion, _) = sampler.best_suggestion(skip=0)
    assert unprocessed_suggestion.get_assignments(experiment)
