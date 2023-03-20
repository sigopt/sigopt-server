# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy

import pytest

from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META, EXPERIMENT_META_MULTIMETRIC
from integration.v1.experiments_test_base import AiExperimentsTestBase


class TestAiExperimentBestTrainingRuns(AiExperimentsTestBase):
  def correct_experiment_meta(self, meta):
    meta = deepcopy(meta)
    meta["budget"] = meta.pop("observation_budget")
    return meta

  @pytest.fixture
  def multimetric_experiment_meta(self):
    return self.correct_experiment_meta(EXPERIMENT_META_MULTIMETRIC)

  def make_training_run(self, connection, ai_experiment, assignments=None, vals=None):
    assignments = {"assignments": assignments} if assignments is not None else {}
    if vals is None:
      vals = [0]
    if isinstance(vals, (int, float)):
      vals = [vals]
    training_run = connection.aiexperiments(ai_experiment.id).training_runs().create(name="dummy-name", **assignments)
    values = {m.name: {"value": val} for m, val in zip(ai_experiment.metrics, vals)}
    training_run_updated = connection.training_runs(training_run.id).update(values=values, state="completed")
    return training_run_updated

  def test_best_training_run_single(self, connection, project):
    ai_experiment = (
      connection.clients(project.client).projects(project.id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)
    )
    _ = self.make_training_run(connection, ai_experiment, vals=0)
    training_run_2 = self.make_training_run(connection, ai_experiment, vals=10)
    _ = self.make_training_run(connection, ai_experiment, vals=5)

    best_training_runs = connection.aiexperiments(ai_experiment.id).best_training_runs().fetch()
    assert best_training_runs is not None
    assert best_training_runs.count == 1
    assert len(best_training_runs.data) == 1
    assert best_training_runs.data[0].id == training_run_2.id

  def test_best_training_run_multimetric(self, connection, multimetric_experiment_meta, project):
    ai_experiment = (
      connection.clients(project.client).projects(project.id).aiexperiments().create(**multimetric_experiment_meta)
    )
    _ = self.make_training_run(connection, ai_experiment, vals=[0, 0])
    training_run_2 = self.make_training_run(connection, ai_experiment, vals=[10, 0])
    training_run_3 = self.make_training_run(connection, ai_experiment, vals=[0, 10])
    training_run_4 = self.make_training_run(connection, ai_experiment, vals=[7, 7])
    _ = self.make_training_run(connection, ai_experiment, vals=[5, 0])
    _ = self.make_training_run(connection, ai_experiment, vals=[0, 5])
    best_training_runs = connection.aiexperiments(ai_experiment.id).best_training_runs().fetch()
    assert best_training_runs is not None
    assert best_training_runs.count == 3
    assert len(best_training_runs.data) == 3
    sorted_ids = sorted(tr.id for tr in best_training_runs.data)
    expected_ids = sorted([training_run_2.id, training_run_3.id, training_run_4.id])
    assert sorted_ids == expected_ids

  def test_best_training_runs_pagination(self, connection, multimetric_experiment_meta, project):
    ai_experiment = (
      connection.clients(project.client).projects(project.id).aiexperiments().create(**multimetric_experiment_meta)
    )
    _ = self.make_training_run(connection, ai_experiment, vals=[0, 0])
    training_run_2 = self.make_training_run(connection, ai_experiment, vals=[10, 0])
    training_run_3 = self.make_training_run(connection, ai_experiment, vals=[0, 10])
    training_run_4 = self.make_training_run(connection, ai_experiment, vals=[7, 7])
    _ = self.make_training_run(connection, ai_experiment, vals=[5, 0])
    _ = self.make_training_run(connection, ai_experiment, vals=[0, 5])

    # confirm limit works
    best_training_runs = connection.aiexperiments(ai_experiment.id).best_training_runs().fetch(limit=1)
    assert best_training_runs.count == 3
    assert len(best_training_runs.data) == 1
    expected_ids = sorted([training_run_2.id, training_run_3.id, training_run_4.id])
    assert best_training_runs.data[0].id in expected_ids

    # confirm all iterated
    best_training_runs = list(
      connection.aiexperiments(ai_experiment.id).best_training_runs().fetch(limit=1).iterate_pages()
    )
    assert len(best_training_runs) == 3
    sorted_ids = sorted(tr.id for tr in best_training_runs)
    assert sorted_ids == expected_ids
