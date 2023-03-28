# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from http import HTTPStatus

import pytest
from libsigopt.sigoptaux.constant import DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS, MAX_NUM_INT_CONSTRAINT_VARIABLES

from zigopt.best_practices.constants import MAX_DIMENSION_WITH_CONSTRAINTS, MAX_OBSERVATIONS_WITH_CONSTRAINTS

from integration.base import RaisesApiException
from integration.v1.constants import EXPERIMENT_META_WITH_CONSTRAINTS
from integration.v1.experiments_test_base import ExperimentFeaturesTestBase


class ExperimentsConstraintsTestBase(ExperimentFeaturesTestBase):
  @pytest.fixture
  def meta(self):
    meta = copy.deepcopy(EXPERIMENT_META_WITH_CONSTRAINTS)
    return meta


class TestConstraintsUpdate(ExperimentsConstraintsTestBase):
  def test_update_constrained_experiment(self, connection, client_id, meta):
    e = connection.clients(client_id).experiments().create(**meta)
    connection.experiments(e.id).update(name="new name")
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(parameters=[dict(name="a", type="double", bounds=dict(min=1, max=50))])
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        linear_constraints=[
          dict(
            type="greater_than",
            terms=[
              dict(name="a", weight=3.4234),
              dict(name="b", weight=3),
            ],
            threshold=4,
          )
        ]
      )

  def test_update_experiment_add_constraints(self, connection, client_id):
    e = connection.create_any_experiment(client_id=client_id)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(e.id).update(
        linear_constraints=[
          dict(
            type="greater_than",
            terms=[
              dict(name="a", weight=3.4234),
              dict(name="b", weight=3),
            ],
            threshold=4,
          )
        ]
      )


class TestConstraintsCreate(ExperimentsConstraintsTestBase):
  @pytest.mark.parametrize(
    "bad_constraint,error_msg",
    [
      ([dict(type="greater_than", terms=[dict(name="f", weight=3)])], "Missing required json key"),
      ([dict(type="linear_eq", terms=[dict(name="f", weight=3)], threshold=4)], "is not one of the allowed values"),
      ([dict(type="greater_than", terms=[dict(name="f")], threshold=4)], "Missing required json key"),
      ([dict(type="greater_than", terms=[dict(name="f", weight=3)], threshold=4, lhs=3)], "Unknown json keys "),
      ([dict(type="greater_than", terms=[dict(name="f", weight=3, hi=1)], threshold=4)], "Unknown json keys"),
    ],
  )
  def test_with_constraints_fail_by_schema_validation(self, connection, client_id, meta, bad_constraint, error_msg):
    meta["linear_constraints"] = bad_constraint
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      connection.clients(client_id).experiments().create(**meta)
    assert error_msg in e.value.message

  @pytest.mark.parametrize(
    "bad_constraint,error_msg",
    [
      (
        [dict(type="greater_than", terms=[dict(name="c", weight=3)], threshold=4)],
        "Variable c is not a parameter of type `double`",
      ),
      (
        [dict(type="greater_than", terms=[dict(name="W", weight=3)], threshold=4)],
        "Variable W is not a known parameter",
      ),
      (
        [dict(type="greater_than", terms=[dict(name="f", weight=3), dict(name="f", weight=4)], threshold=4)],
        "Duplicate variable name: f",
      ),
      ([dict(type="greater_than", terms=[dict(name="f")], threshold=4)], "Missing required json key"),
      ([dict(type="greater_than", terms=[], threshold=4)], "Constraint must have at least one term"),
      (
        [
          dict(type="greater_than", terms=[dict(name="f", weight=1), dict(name="b", weight=1)], threshold=0),
          dict(type="greater_than", terms=[dict(name="f", weight=-1), dict(name="b", weight=-1)], threshold=0),
        ],
        "Infeasible constraints or empty set",
      ),
      (
        [
          dict(type="greater_than", terms=[dict(name="f", weight=1), dict(name="b", weight=1)], threshold=0.5),
          dict(type="less_than", terms=[dict(name="f", weight=1), dict(name="b", weight=1)], threshold=0.5),
        ],
        "Infeasible constraints or empty set",
      ),
      (
        [dict(type="greater_than", terms=[dict(name="f", weight=1)], threshold=23)],
        "Constraints should affect at least two parameters",
      ),
      (
        [dict(type="greater_than", terms=[dict(name="a", weight=3)], threshold=4)],
        "Constraints should affect at least two parameters",
      ),
      (
        [dict(type="greater_than", terms=[dict(name="f", weight=1), dict(name="b", weight=0)], threshold=23)],
        "Constraints should affect at least two parameters",
      ),
      (
        [dict(type="greater_than", terms=[dict(name="a", weight=0), dict(name="g", weight=0)], threshold=23)],
        "Constraints should affect at least two parameters",
      ),
      (
        [dict(type="greater_than", terms=[dict(name="a", weight=1), dict(name="b", weight=1)], threshold=23)],
        "Constraint functions cannot mix integers and doubles. One or the other only.",
      ),
    ],
  )
  def test_with_constraints_fail_with_params(self, connection, client_id, meta, bad_constraint, error_msg):
    meta["linear_constraints"] = bad_constraint
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      connection.clients(client_id).experiments().create(**meta)
    assert error_msg in e.value.message


class TestConstraintsBestPractices(ExperimentsConstraintsTestBase):
  def test_max_dimension(self, connection, client_id, meta):
    meta["parameters"].extend(
      [
        dict(
          type="double",
          bounds=dict(min=0, max=1),
          name=f"x{i}",
        )
        for i in range(MAX_DIMENSION_WITH_CONSTRAINTS - len(meta["parameters"]))
      ]
    )

    e = connection.clients(client_id).experiments().create(**meta)

    assert len(e.parameters) == MAX_DIMENSION_WITH_CONSTRAINTS

  def test_max_observation_budget(self, connection, client_id, meta):
    meta["observation_budget"] = MAX_OBSERVATIONS_WITH_CONSTRAINTS
    e = connection.clients(client_id).experiments().create(**meta)

    assert e.observation_budget == MAX_OBSERVATIONS_WITH_CONSTRAINTS

  def test_max_open_suggestions(self, connection, client_id, meta):
    parallel_bandwidth = len(meta["parameters"])
    meta["parallel_bandwidth"] = None

    e = connection.clients(client_id).experiments().create(**meta)
    for _ in range(parallel_bandwidth):
      connection.experiments(e.id).suggestions().create()

    assert connection.experiments(e.id).suggestions().fetch(state="open", limit=0).count == parallel_bandwidth

  def test_max_parallel_bandwidth(self, connection, client_id, meta):
    parallel_bandwidth = len(meta["parameters"])
    meta["parallel_bandwidth"] = parallel_bandwidth

    e = connection.clients(client_id).experiments().create(**meta)

    assert e.parallel_bandwidth == parallel_bandwidth


class TestConstraintsManualAssignments(ExperimentsConstraintsTestBase):
  @pytest.fixture(
    params=[
      dict(a=1, b=0, c="d", f=2, g=12),
      dict(a=1, b=-1, c="d", f=14, g=4),
    ]
  )
  def assignments(self, request):
    return request.param

  @pytest.fixture(
    params=[
      dict(a=50, b=-50, c="d", f=2, g=10),
      dict(a=25, b=-3, c="e", f=50, g=25),
    ]
  )
  def invalid_assignments(self, request):
    return request.param

  @pytest.fixture
  def experiment(self, connection, client_id, meta):
    return connection.clients(client_id).experiments().create(**meta)

  def test_create_observation(self, connection, experiment, assignments):
    connection.experiments(experiment.id).observations().create(assignments=assignments, values=[{"value": 0}])

  def test_create_queued_suggestion(self, connection, experiment, assignments):
    connection.experiments(experiment.id).queued_suggestions().create(assignments=assignments)

  def test_create_suggestion(self, connection, experiment, assignments):
    connection.experiments(experiment.id).suggestions().create(assignments=assignments)

  def test_create_observation_invalid_assignment(self, connection, experiment, invalid_assignments):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).observations().create(
        assignments=invalid_assignments, values=[{"value": 0}]
      )

  def test_create_queued_suggestion_invalid_assignment(self, connection, experiment, invalid_assignments):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).queued_suggestions().create(assignments=invalid_assignments)

  def test_create_suggestion_invalid_assignment(self, connection, experiment, invalid_assignments):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).suggestions().create(assignments=invalid_assignments)


class TestConstraintsOptimize(ExperimentsConstraintsTestBase):
  def test_optimize(self, services, connection, client_id, meta):
    num_params_to_add = DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS - len(meta["parameters"])
    meta["parameters"].extend(
      [dict(name=f"p{i}", type="double", bounds=dict(min=0, max=1)) for i in range(num_params_to_add)]
    )

    meta["observation_budget"] = 2
    e = connection.clients(client_id).experiments().create(**meta)
    s = connection.experiments(e.id).suggestions().create()
    connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 0}])

    experiment = services.experiment_service.find_by_id(int(e.id))
    assert services.optimizer.should_use_spe(experiment, 1)
    s = connection.experiments(e.id).suggestions().create()
    connection.experiments(e.id).observations().create(suggestion=s.id, values=[{"value": 0}], no_optimize=False)


class TestConstraintsDifferentCases(ExperimentsConstraintsTestBase):
  def _test_experiment_success(self, meta, connection, client_id):
    e = connection.clients(client_id).experiments().create(**meta)
    s = connection.experiments(e.id).suggestions().create()
    for parameter in meta["parameters"]:
      assert parameter["name"] in s.assignments

  @pytest.mark.parametrize(
    "constraints",
    [
      [
        dict(type="less_than", threshold=10, terms=[dict(name=f"double_{i}", weight=1) for i in range(2)]),
      ],
      [
        dict(type="less_than", threshold=10, terms=[dict(name=f"double_{i}", weight=1) for i in range(2)]),
        dict(type="less_than", threshold=10, terms=[dict(name=f"double_{i}", weight=1) for i in range(4)]),
      ],
    ],
  )
  def test_constraints_experiment(self, connection, client_id, constraints):
    base_meta = dict(
      name="Test Experiment",
      parameters=[dict(name=f"double_{i}", type="double", bounds=dict(min=0, max=3)) for i in range(4)],
      metrics=[dict(name="holdout_accuracy", strategy="optimize", objective="maximize")],
      parallel_bandwidth=1,
      observation_budget=7,
    )
    modified_meta = copy.deepcopy(base_meta)
    modified_meta["linear_constraints"] = constraints
    self._test_experiment_success(modified_meta, connection, client_id)


class TestTooManyConstrainedVariables(ExperimentsConstraintsTestBase):
  def test_fail_when_too_many_integer_constrained_variables(self, connection, client_id):
    experiment_meta = dict(
      name="default constrained experiment",
      metrics=[dict(name="profit")],
      observation_budget=30,
      parameters=[
        dict(name=f"x{i}", type="int", bounds=dict(min=1, max=50)) for i in range(MAX_NUM_INT_CONSTRAINT_VARIABLES + 1)
      ],
      linear_constraints=[
        dict(
          type="greater_than",
          terms=[dict(name=f"x{i}", weight=1) for i in range(MAX_NUM_INT_CONSTRAINT_VARIABLES + 1)],
          threshold=4,
        ),
      ],
    )
    error_msg = f"SigOpt allows no more than {MAX_NUM_INT_CONSTRAINT_VARIABLES} integer constraint variables"
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      connection.clients(client_id).experiments().create(**experiment_meta)
    assert error_msg in e.value.message
