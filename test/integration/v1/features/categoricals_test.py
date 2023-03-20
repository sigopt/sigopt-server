# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from time import sleep

from integration.utils.random_assignment import random_assignments
from integration.v1.test_base import V1Base


class TestCategoricalExperiments(V1Base):
  def test_update_categorical_values(self, connection):
    starting_meta = {
      "name": "cat test",
      "parameters": [
        {"name": "d", "type": "double", "bounds": {"min": 0, "max": 1}},
        {"name": "i", "type": "int", "bounds": {"min": -4, "max": 3}},
        {
          "name": "c1",
          "type": "categorical",
          "categorical_values": [{"name": "c1a"}, {"name": "c1b"}],
        },
        {
          "name": "c2",
          "type": "categorical",
          "categorical_values": [{"name": "c2a"}, {"name": "c2b"}, {"name": "c2c"}],
        },
      ],
    }

    updated_meta = {
      "name": "cat test",
      "parameters": [
        {"name": "d", "type": "double", "bounds": {"min": 0, "max": 1}},
        {"name": "i", "type": "int", "bounds": {"min": -4, "max": 3}},
        {
          "name": "c1",
          "type": "categorical",
          "categorical_values": [{"name": "c1a"}, {"name": "c1b"}, {"name": "c1c"}],
        },
        {"name": "c2", "type": "categorical", "categorical_values": [{"name": "c2a"}, {"name": "c2b"}]},
      ],
    }

    e = connection.clients(connection.client_id).experiments().create(**starting_meta)

    # Put enough data in to start considering hyperparameter optimization
    for k in range(14):
      connection.experiments(e.id).observations().create(
        assignments=random_assignments(e),
        values=[{"value": k}],
        no_optimize=True,
      )

    # Trigger the hyperparameter optimization to store hyperparameters that will go out of date
    connection.experiments(e.id).observations().create(
      assignments=random_assignments(e),
      values=[{"value": 0}],
      no_optimize=False,
    )

    # Make the hyperparameters out of date
    connection.experiments(e.id).update(**updated_meta)

    # Confirm that the old hyperparameters are not destroying anything (would have crashed before)
    suggestion = connection.experiments(e.id).suggestions().create()
    connection.experiments(e.id).observations().create(
      assignments=suggestion.assignments,
      values=[{"value": 0}],
      no_optimize=False,
    )

    for k in range(5):
      suggestion = connection.experiments(e.id).suggestions().create()
      assert 0 <= suggestion.assignments["d"] <= 1
      assert -4 <= suggestion.assignments["i"] <= 3
      assert suggestion.assignments["c1"] in ["c1a", "c1b", "c1c"]
      assert suggestion.assignments["c2"] in ["c2a", "c2b"]
      connection.experiments(e.id).observations().create(suggestion=suggestion.id, values=[{"value": k}])

    # The next points for this test is relatively slow - needed to avoid intermittent CI Failure
    sleep(10)

  def test_oversampling_discrete_after_update(self, connection):
    experiment_meta = {
      "name": "cat test",
      "parameters": [
        {
          "name": "c1",
          "type": "categorical",
          "categorical_values": [{"name": "a"}, {"name": "b"}, {"name": "c"}],
        },
      ],
    }
    e = connection.clients(connection.client_id).experiments().create(**experiment_meta)
    for k in range(5):
      suggestion = connection.experiments(e.id).suggestions().create()
      assert suggestion.assignments["c1"] in ["a", "b", "c"]
      connection.experiments(e.id).observations().create(suggestion=suggestion.id, values=[{"value": k}])

    updated_meta = {
      "name": "cat test",
      "parameters": [
        {
          "name": "c1",
          "type": "categorical",
          "categorical_values": [{"name": "a"}, {"name": "c"}],
        },
      ],
    }
    connection.experiments(e.id).update(**updated_meta)

    for k in range(5):
      suggestion = connection.experiments(e.id).suggestions().create()
      assert suggestion.assignments["c1"] in ["a", "c"]
      connection.experiments(e.id).observations().create(suggestion=suggestion.id, values=[{"value": k}])

    a = connection.experiments(e.id).best_assignments().fetch()
    assert a.count == 1
    assert a.data[0].values[0].value == 4

    # The next points for this test is relatively slow - needed to avoid intermittent CI Failure
    sleep(5)
