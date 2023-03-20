# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.experiment.model import Experiment
from zigopt.experiment.progress import ExperimentObservationProgress, ExperimentRunProgress
from zigopt.json.builder.experiment import *
from zigopt.observation.model import Observation
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentMeta
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData


def set_as_maybe_none(obj, attr, value):
  if value is None:
    obj.ClearField(attr)
  else:
    setattr(obj, attr, value)


class TestExperimentJsonBuilder(object):
  @pytest.mark.parametrize("metric_name", [None, ""])
  @pytest.mark.parametrize("value_name", [None, ""])
  @pytest.mark.parametrize("num_metrics", [1, 2])
  def test_no_metric_name_returned_as_null(self, metric_name, value_name, num_metrics):
    experiment_meta = ExperimentMeta()
    experiment_meta.metrics.add()
    set_as_maybe_none(experiment_meta.metrics[0], "name", metric_name)

    observation_data = ObservationData()
    observation_data.values.add()
    set_as_maybe_none(observation_data.values[0], "name", metric_name)

    if num_metrics == 2:
      experiment_meta.metrics.add()
      experiment_meta.metrics[1].name = "other"
      observation_data.values.add()
      observation_data.values[1].name = "other"

    e = Experiment(experiment_meta=experiment_meta)
    o = Observation(data=observation_data)

    progress = ExperimentObservationProgress(e, None, None, o, 1, 1)
    json = ExperimentJsonBuilder(e, progress_builder=progress.json_builder()).resolve_all()
    assert len(json["metrics"]) == num_metrics
    assert json["metrics"][0]["name"] is None
    assert len(json["progress"]["last_observation"]["values"]) == num_metrics
    assert json["progress"]["last_observation"]["values"][0]["name"] is None

  def test_run_progress_builder(self):
    experiment_meta = ExperimentMeta()
    experiment_meta.observation_budget = 5 + 7 + 13

    e = Experiment(experiment_meta=experiment_meta)
    progress = ExperimentRunProgress(e, finished_run_count=7, active_run_count=5)
    progress_builder = progress.json_builder()
    progress_data = progress_builder.resolve_all()
    assert progress_data["object"] == "progress"
    assert progress_data["finished_run_count"] == 7
    assert progress_data["active_run_count"] == 5
    assert progress_data["total_run_count"] == 12
    assert progress_data["remaining_budget"] == 13
