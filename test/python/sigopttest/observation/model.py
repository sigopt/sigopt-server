# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.experiment.model import Experiment
from zigopt.observation.model import Observation, ObservationDataProxy
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  MAXIMIZE,
  MINIMIZE,
  PARAMETER_CATEGORICAL,
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  ExperimentMeta,
  ExperimentMetric,
)
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData, ObservationValue


class TestParameters:
  @pytest.fixture
  def experiment(self):
    experiment_meta = ExperimentMeta()

    p = experiment_meta.all_parameters_unsorted.add()
    p.name = "p1"
    p.param_type = PARAMETER_DOUBLE
    p.bounds.minimum = 1
    p.bounds.maximum = 2

    p = experiment_meta.all_parameters_unsorted.add()
    p.name = "p2"
    p.param_type = PARAMETER_INT
    p.bounds.minimum = 3
    p.bounds.maximum = 4

    p = experiment_meta.all_parameters_unsorted.add()
    p.name = "p3"
    p.param_type = PARAMETER_CATEGORICAL
    cat = p.all_categorical_values.add()
    cat.name = "True"
    cat.enum_index = 0
    cat = p.all_categorical_values.add()
    cat.name = "False"
    cat.enum_index = 1

    p = experiment_meta.all_parameters_unsorted.add()
    p.name = "p4"
    p.param_type = PARAMETER_DOUBLE
    p.bounds.minimum = 0
    p.bounds.maximum = 1
    p.replacement_value_if_missing = 0.5

    p = experiment_meta.all_parameters_unsorted.add()
    p.name = "p5"
    p.param_type = PARAMETER_DOUBLE
    p.bounds.minimum = 0
    p.bounds.maximum = 1
    p.deleted = True

    p = experiment_meta.all_parameters_unsorted.add()
    p.name = "p6"
    p.param_type = PARAMETER_DOUBLE
    p.grid_values.extend([-0.2, 0.0, 0.3, 1.2, 1.63])

    return Experiment(experiment_meta=experiment_meta)

  def test_observation_with_parameters(self, experiment):
    observation_data = ObservationData(assignments_map=dict(p1=2, p2=3, p3=1, p5=1, p6=0.3))
    proxy = ObservationDataProxy(observation_data)
    observation = Observation(data=proxy)

    assert sorted(proxy.get_assignments(experiment).keys()) == ["p1", "p2", "p3", "p4", "p6"]

    assert observation.get_assignment(experiment.all_parameters[0]) == 2
    assert observation.get_assignment(experiment.all_parameters[1]) == 3
    assert observation.get_assignment(experiment.all_parameters[2]) == 1
    assert observation.get_assignment(experiment.all_parameters[3]) == 0.5
    assert observation.get_assignment(experiment.all_parameters_including_deleted[4]) is None
    assert observation.get_assignment(experiment.all_parameters[4]) == 0.3

    assignments_map = observation.get_assignments(experiment)
    assert len(assignments_map) == 5
    assert assignments_map["p1"] == 2
    assert assignments_map["p2"] == 3
    assert assignments_map["p3"] == 1
    assert assignments_map["p4"] == 0.5
    assert assignments_map["p6"] == 0.3
    # pylint: disable=pointless-statement
    with pytest.raises(KeyError):
      assignments_map["p5"]
    # pylint: enable=pointless-statement

  def test_observation_non_categorical_violate_bounds(self, experiment):
    observation_data = ObservationData(assignments_map=dict(p1=2.1, p2=3.5, p3=2, p5=22, p6=0.31))
    proxy = ObservationDataProxy(observation_data)
    observation = Observation(data=proxy)

    assert sorted(proxy.get_assignments(experiment).keys()) == ["p1", "p2", "p3", "p4", "p6"]

    assert observation.get_assignment(experiment.all_parameters[0]) == 2.1
    assert observation.get_assignment(experiment.all_parameters[1]) == 3.5
    assert observation.get_assignment(experiment.all_parameters[2]) == 2
    assert observation.get_assignment(experiment.all_parameters[3]) == 0.5
    assert observation.get_assignment(experiment.all_parameters_including_deleted[4]) is None
    assert observation.get_assignment(experiment.all_parameters[4]) == 0.31

    assignments_map = observation.get_assignments(experiment)
    assert len(assignments_map) == 5
    assert assignments_map["p1"] == 2.1
    assert assignments_map["p2"] == 3.5
    assert assignments_map["p3"] == 2
    assert assignments_map["p4"] == 0.5
    assert assignments_map["p6"] == 0.31
    # pylint: disable=pointless-statement
    with pytest.raises(KeyError):
      assignments_map["p5"]
    # pylint: enable=pointless-statement


class TestInMetricThresholds:
  @pytest.fixture
  def comparison(self, request):
    metric_1, metric_2 = request.param
    objective_1, threshold_1, metric_value_1 = metric_1
    objective_2, threshold_2, metric_value_2 = metric_2
    metric_1 = ExperimentMetric(
      name="metric_1",
      objective=objective_1,
      threshold=threshold_1,
    )
    metric_2 = ExperimentMetric(
      name="metric_2",
      objective=objective_2,
      threshold=threshold_2,
    )
    experiment_meta = ExperimentMeta(
      metrics=[
        metric_1,
        metric_2,
      ]
    )
    experiment = Experiment(experiment_meta=experiment_meta)

    observation_data = ObservationData(
      values=[
        ObservationValue(
          name="metric_1",
          value=metric_value_1,
        ),
        ObservationValue(
          name="metric_2",
          value=metric_value_2,
        ),
      ]
    )
    proxy = ObservationDataProxy(observation_data)
    observation = Observation(data=proxy)

    return observation, experiment

  @pytest.mark.parametrize(
    "comparison",
    # (objective1, threshold1, value1), (objective2, threshold2, value2)
    [
      ((MAXIMIZE, None, -999.9), (MINIMIZE, None, 999.9)),
      ((MAXIMIZE, 1.0, 30.1), (MINIMIZE, 0.5, 0.2)),
      ((MAXIMIZE, 1.0, 1.5), (MAXIMIZE, 0.1, 0.4)),
      ((MAXIMIZE, None, 30.1), (MAXIMIZE, 0.1, 0.2)),
      ((MINIMIZE, 40.0, 1.5), (MINIMIZE, None, 0.4)),
      ((MINIMIZE, None, 30.1), (MINIMIZE, 40.0, 0.2)),
    ],
    indirect=True,
  )
  def test_observation_within_thresholds(self, comparison):
    observation, experiment = comparison
    assert observation.within_metric_thresholds(experiment)

  @pytest.mark.parametrize(
    "comparison",
    # (objective1, threshold1, value1), (objective2, threshold2, value2)
    [
      ((MAXIMIZE, 0.0, 444.3), (MINIMIZE, 0.5, None)),
      ((MAXIMIZE, 0.0, None), (MINIMIZE, 0.5, 0.6)),
      ((MAXIMIZE, 0.0, 444.3), (MINIMIZE, 0.5, 1.0)),
      ((MAXIMIZE, 0.0, -2.0), (MINIMIZE, 0.5, 0.0)),
      ((MINIMIZE, 1.0, None), (MAXIMIZE, 2.0, 0.6)),
      ((MINIMIZE, 1.0, None), (MAXIMIZE, 2.0, None)),
      ((MINIMIZE, 1.0, 444.3), (MAXIMIZE, 2.0, 3.0)),
      ((MINIMIZE, 1.0, 0.5), (MAXIMIZE, 2.0, 0.6223)),
    ],
    indirect=True,
  )
  def test_observation_out_of_thresholds(self, comparison):
    observation, experiment = comparison
    assert not observation.within_metric_thresholds(experiment)

  @pytest.mark.parametrize(
    "comparison",
    # (objective1, threshold1, value1), (objective2, threshold2, value2)
    [
      ((MAXIMIZE, 0.0, None), (MINIMIZE, 0.5, 0.6)),
    ],
    indirect=True,
  )
  def test_metric_value(self, comparison):
    observation, experiment = comparison
    assert observation.metric_value(experiment, "metric_1") is None
    assert observation.metric_value(experiment, "metric_2") == 0.6
