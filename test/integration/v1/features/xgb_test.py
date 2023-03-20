# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy

import pytest

from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.v1.test_base import V1Base


xgb_experiment_meta = dict(
  name="XGB Experiment",
  parameters=[
    dict(name="gamma", type="double", bounds={"min": 0, "max": 10}),
    dict(name="max_depth", type="int", bounds={"min": 10, "max": 20}),
    dict(name="min_child_weight", type="double", bounds={"min": 1, "max": 5}),
    dict(name="lambda", type="double", bounds={"min": 1, "max": 5}),
    dict(name="booster", type="categorical", categorical_values=["gbtree", "gblinear", "dart"]),
  ],
  metadata={"_IS_XGB_EXPERIMENT": "True"},
)


class TestXGBExperiment(V1Base):
  @pytest.fixture
  def client_id(self, connection):
    return connection.client_id

  def check_suggestions_correct_type(self, meta, connection, client_id):
    e = connection.clients(client_id).experiments().create(**meta)
    n_suggestions = 12
    for _ in range(n_suggestions):
      s = connection.experiments(e.id).suggestions().create()
      for parameter in meta["parameters"]:
        param_name = parameter["name"]
        if parameter["type"] == "double":
          assert isinstance(s.assignments[param_name], float)
        if parameter["type"] == "int":
          assert isinstance(s.assignments[param_name], int)
        if parameter["type"] == "categorical":
          assert isinstance(s.assignments[param_name], str)
      connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 0}])

  def check_suggestions_in_bounds(self, meta, connection, client_id):
    e = connection.clients(client_id).experiments().create(**meta)
    n_suggestions = 12
    for _ in range(n_suggestions):
      s = connection.experiments(e.id).suggestions().create()
      for parameter in meta["parameters"]:
        param_name = parameter["name"]
        if parameter["type"] == "double" or parameter["type"] == "int":
          assert s.assignments[param_name] >= parameter["bounds"]["min"]
          assert s.assignments[param_name] <= parameter["bounds"]["max"]
        if parameter["type"] == "categorical":
          assert s.assignments[param_name] in parameter["categorical_values"]
      connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 0}])

  def test_experiment_integrity(self, connection, client_id):
    e = connection.clients(client_id).experiments().create(**xgb_experiment_meta)
    param_map = dict((p.name, p) for p in e.parameters)
    assert param_map["gamma"]
    assert param_map["max_depth"]
    assert param_map["min_child_weight"]
    assert param_map["lambda"]
    assert param_map["booster"]

  def test_experiment_source(self, connection, client_id, services):
    e = connection.clients(client_id).experiments().create(**xgb_experiment_meta)
    n_suggestions = 2
    for _ in range(n_suggestions):
      s = connection.experiments(e.id).suggestions().create()
      unprocessed_suggestion = services.unprocessed_suggestion_service.find_by_id(s.id)
      assert unprocessed_suggestion.source == UnprocessedSuggestion.Source.XGB
      connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 0}])

  def test_experiment_after_prior_not_xgb_source(self, connection, client_id, services):
    e = connection.clients(client_id).experiments().create(**xgb_experiment_meta)
    n_suggestions = 20
    for i in range(n_suggestions - 1):
      s = connection.experiments(e.id).suggestions().create()
      if i < n_suggestions - 2:
        connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": i}], no_optimize=True)
      else:
        connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": i}])

    s = connection.experiments(e.id).suggestions().create()
    unprocessed_suggestion = services.unprocessed_suggestion_service.find_by_id(s.id)
    assert unprocessed_suggestion.source != UnprocessedSuggestion.Source.XGB

  def test_experiment_bounds(self, connection, client_id):
    self.check_suggestions_in_bounds(xgb_experiment_meta, connection, client_id)

  def test_experiment_types(self, connection, client_id):
    self.check_suggestions_correct_type(xgb_experiment_meta, connection, client_id)

  def test_num_boost_round(self, connection, client_id, services):
    meta = copy.deepcopy(xgb_experiment_meta)
    meta["parameters"].append(dict(name="num_boost_round", type="int", bounds={"min": 10, "max": 100}))
    self.check_suggestions_in_bounds(meta, connection, client_id)

  def test_experiment_small_bounds(self, connection, client_id, services):
    meta = copy.deepcopy(xgb_experiment_meta)
    meta["parameters"].append(dict(name="eta", type="double", bounds={"min": 0.1, "max": 0.100001}))
    self.check_suggestions_in_bounds(meta, connection, client_id)

  def test_experiment_out_of_prior_bounds(self, connection, client_id, services):
    meta = copy.deepcopy(xgb_experiment_meta)
    meta["parameters"].append(dict(name="eta", type="double", bounds={"min": 11, "max": 20}))
    self.check_suggestions_in_bounds(meta, connection, client_id)

  def test_experiment_log_scaling(self, connection, client_id, services):
    meta = copy.deepcopy(xgb_experiment_meta)
    meta["parameters"].append(dict(name="eta", type="double", bounds={"min": 0.1, "max": 1}, transform="log"))
    self.check_suggestions_in_bounds(meta, connection, client_id)

  def test_experiment_active_prior(self, connection, client_id, services):
    """
        Check that priors are actually active. This is done by verifying no samples are outside prior bounds, despite
        max user-set bounds that are much, much larger. NOTE: This test is probabilistic by nature, and therefore
        could, with very low probability, fail. The large majority of the
        """
    meta = dict(
      name="XGB Experiment",
      parameters=[
        dict(name="min_child_weight", type="double", bounds={"min": 0.1, "max": 1000}),
        dict(name="max_delta_step", type="double", bounds={"min": 0.1, "max": 2000}),
      ],
      metadata={"_IS_XGB_EXPERIMENT": "True"},
    )
    e = connection.clients(client_id).experiments().create(**meta)
    n_suggestions = 4
    for _ in range(n_suggestions):
      s = connection.experiments(e.id).suggestions().create()
      assert s.assignments["min_child_weight"] < 6  # min_child_weight prior pdf supported over [0, 5]
      assert s.assignments["max_delta_step"] < 11  # max_delta_step prior pdf supported over [0, 10]
      connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 0}])

  def test_all_priors_simultanously(self, connection, client_id, services):
    meta = dict(
      name="XGB Experiment",
      parameters=[
        dict(name="gamma", type="double", bounds={"min": 0, "max": 10}),
        dict(name="max_depth", type="int", bounds={"min": 10, "max": 20}),
        dict(name="min_child_weight", type="double", bounds={"min": 1, "max": 5}),
        dict(name="lambda", type="double", bounds={"min": 1, "max": 5}),
        dict(name="num_boost_round", type="int", bounds={"min": 1, "max": 500}),
        dict(name="eta", type="double", bounds={"min": 0.0001, "max": 1}),
      ],
      metadata={"_IS_XGB_EXPERIMENT": "True"},
    )
    self.check_suggestions_in_bounds(meta, connection, client_id)
