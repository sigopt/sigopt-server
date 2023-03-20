# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# -*- coding: utf-8 -*-
import copy
from http import HTTPStatus

import pytest
from flaky import flaky

from zigopt.math.initialization import get_low_discrepancy_stencil_length_from_experiment
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.base import RaisesApiException
from integration.v1.constants import EXPERIMENT_META_CONDITIONALS, EXPERIMENT_META_MULTICONDITIONAL
from integration.v1.experiments_test_base import ExperimentFeaturesTestBase


class ExperimentsConditionalsTestBase(ExperimentFeaturesTestBase):
  @pytest.fixture
  def meta(self, connection):
    meta = copy.deepcopy(EXPERIMENT_META_CONDITIONALS)
    return meta

  @pytest.fixture
  def experiment(self, connection, client_id, meta):
    return connection.clients(client_id).experiments().create(**meta)


class TestConditionalsCreate(ExperimentsConditionalsTestBase):
  def test_create_multi_conditional(self, connection, client_id):
    connection.clients(client_id).experiments().create(**EXPERIMENT_META_MULTICONDITIONAL)

  def test_create_with_conditionals(self, connection, client_id, meta):
    experiment = connection.clients(client_id).experiments().create(**meta)
    (x,) = experiment.conditionals
    assert x.name == "x"
    assert sorted(x.values) == sorted(["1", "5", "10"])

  def test_explicit_parameter_conditions(self, connection, client_id, meta):
    meta["parameters"][0]["conditions"] = dict(x=["1", "5", "10"])
    meta["parameters"][1]["conditions"] = dict(x=["5", "10"])
    meta["parameters"][2]["conditions"] = dict(x="10")

    connection.clients(client_id).experiments().create(**meta)

  def test_implicit_parameter_conditions(self, connection, client_id, meta):
    meta["parameters"][0]["conditions"] = dict()
    meta["parameters"][1]["conditions"] = dict(x=["5", "10"])
    meta["parameters"][2]["conditions"] = dict(x="10")

    connection.clients(client_id).experiments().create(**meta)

  def test_cannot_create_grid_search(self, connection, client_id, meta):
    meta["parameters"][0].pop("bounds")
    meta["parameters"][1].pop("bounds")
    meta["parameters"][0]["grid"] = [1, 2, 3]
    meta["parameters"][1]["grid"] = [-35.2, 23.5]
    meta["type"] = "grid"
    meta.pop("observation_budget")
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_create_with_overlapping_names(self, connection, client_id, meta):
    meta["parameters"][1]["name"] = meta["conditionals"][0]["name"]
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  @pytest.mark.parametrize("conditions_json", [dict(x="9"), dict(x=["1", "9"]), dict(z="5")])
  def test_create_with_invalid_parameter_conditions(self, connection, client_id, conditions_json, meta):
    meta["parameters"][0]["conditions"] = conditions_json
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_create_insufficient_conditions(self, connection, client_id, meta):
    for parameter in meta["parameters"]:
      parameter["conditions"] = dict(x="1")
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)


class TestMultipleConditionalsCreate(ExperimentsConditionalsTestBase):
  @pytest.fixture
  def meta(self, connection):
    meta = copy.deepcopy(EXPERIMENT_META_CONDITIONALS)
    meta["conditionals"] = [
      dict(name="x", values=["5", "10"]),
      dict(name="y", values=["true", "false"]),
    ]
    return meta

  def test_conditions_mixed(self, connection, client_id, meta):
    meta["parameters"][0]["conditions"] = dict(y="true")
    meta["parameters"][1]["conditions"] = dict(x=["5", "10"])
    meta["parameters"][2]["conditions"] = dict(x="10")

    experiment = connection.clients(client_id).experiments().create(**meta)

    (a, b, c) = sorted(experiment.parameters, key=lambda p: p.name)
    assert len(a.conditions) == 1
    assert a.conditions["y"] == ["true"]
    assert len(b.conditions) == 1
    assert sorted(b.conditions["x"]) == sorted(["5", "10"])
    assert len(c.conditions) == 1
    assert c.conditions["x"] == ["10"]

  def test_conditions_implicit(self, connection, client_id, meta):
    meta["parameters"][0]["conditions"] = dict(x=["5"])
    meta["parameters"][1]["conditions"] = dict(x=["5", "10"])
    meta["parameters"][2]["conditions"] = dict(x="10")

    connection.clients(client_id).experiments().create(**meta)

  def test_conditions_explicit(self, connection, client_id, meta):
    meta["parameters"][0]["conditions"] = dict(x="5", y="true")
    meta["parameters"][1]["conditions"] = dict(x=["5", "10"], y="false")
    meta["parameters"][2]["conditions"] = dict(x="10", y="true")

    connection.clients(client_id).experiments().create(**meta)

  def test_unsatisfied_conditions_explicit(self, connection, client_id, meta):
    meta["parameters"][0]["conditions"] = dict(x="5", y="true")
    meta["parameters"][1]["conditions"] = dict(x="10", y="false")
    meta["parameters"][2]["conditions"] = dict(x="10", y="true")

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)

  def test_unsatisfied_conditions_implicit(self, connection, client_id, meta):
    meta["parameters"][0]["conditions"] = dict(x="10")
    meta["parameters"][1]["conditions"] = dict(x="10")
    meta["parameters"][2]["conditions"] = dict(x="10")

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.clients(client_id).experiments().create(**meta)


class TestConditionalsUpdate(ExperimentsConditionalsTestBase):
  @pytest.mark.parametrize(
    "conditionals_json",
    [
      [dict(name="x", values=["true", "false"])],
      [dict(name="y", values=["true", "false"])],
    ],
  )
  def test_update_experiment_conditionals(self, connection, client_id, experiment, conditionals_json):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).update(conditionals=conditionals_json)

  @pytest.mark.parametrize(
    "conditions_json",
    [
      dict(x=["true", "false"]),
      dict(y=["true", "false"]),
    ],
  )
  def test_update_parameter_conditions(self, connection, client_id, experiment, conditions_json):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.experiments(experiment.id).update(parameters=dict(name="a", conditions=conditions_json))


class TestConditionalsAssignments(ExperimentsConditionalsTestBase):
  def ensure_valid_assignments(self, assignments):
    x = assignments["x"]
    assert x in ["1", "5", "10"]
    if x == "1":
      assert len(assignments) == 2
      assert 1 <= assignments["a"] <= 50
      assert "b" not in assignments
      assert "c" not in assignments
    elif x == "5":
      assert len(assignments) == 3
      assert 1 <= assignments["a"] <= 50
      assert -50 <= assignments["b"] <= 0
      assert "c" not in assignments
    elif x == "10":
      assert len(assignments) == 4
      assert 1 <= assignments["a"] <= 50
      assert -50 <= assignments["b"] <= 0
      assert assignments["c"] in ["d", "e"]

  @pytest.mark.parametrize("delete", [True, False])
  def test_create_suggestion(self, connection, client_id, experiment, delete):
    for _ in range(4):
      suggestion = connection.experiments(experiment.id).suggestions().create()
      self.ensure_valid_assignments(suggestion.assignments)
      if delete:
        connection.experiments(experiment.id).suggestions(suggestion.id).delete()

  def test_create_observation(self, connection, client_id, experiment):
    suggestion = connection.experiments(experiment.id).suggestions().create()
    observation = (
      connection.experiments(experiment.id).observations().create(suggestion=suggestion.id, values=[{"value": 1}])
    )
    assert suggestion.assignments == observation.assignments


class TestConditionalsInvalidAssignments(ExperimentsConditionalsTestBase):
  @pytest.fixture(
    params=[
      (dict(x=3, a=50, b=0, c="d"), "invalid"),
      (dict(x=2, a=50, b=0), "invalid"),
      (dict(x=1, a=50), "invalid"),
      (dict(x="1", a=50, c="d"), "unsatisfied"),
      (dict(x="1", a=50, b=0), "unsatisfied"),
      (dict(x="5", a=50, b=0, c="d"), "unsatisfied"),
      (dict(x="1", a=50, b=None, c="d"), "missing"),  # TODO: we expect this error to be 'unsatisfied'
      (dict(x="10", c="d"), "missing"),
      (dict(x="10", a=None, b=None, c="d"), "missing"),
    ]
  )
  def assignments_and_errors(self, request):
    return request.param

  @pytest.fixture
  def assignments(self, assignments_and_errors):
    return assignments_and_errors[0]

  @pytest.fixture
  def expected_error(self, assignments_and_errors):
    return assignments_and_errors[1]

  def test_suggestion_invalid_assignments(self, connection, client_id, experiment, assignments, expected_error):
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      connection.experiments(experiment.id).suggestions().create(assignments=assignments)
    assert expected_error in str(e).lower()

  def test_create_observation_invalid_assignments(self, connection, client_id, experiment, assignments, expected_error):
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      connection.experiments(experiment.id).observations().create(assignments=assignments, values=[{"value": 1}])
    assert expected_error in str(e).lower()

  def test_update_observation_invalid_assignments(self, connection, client_id, experiment, assignments, expected_error):
    s = connection.experiments(experiment.id).suggestions().create()
    o = connection.experiments(experiment.id).observations().create(assignments=s.assignments, values=[{"value": 1}])
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      connection.experiments(experiment.id).observations(o.id).update(assignments=assignments)
    assert expected_error in str(e).lower()

  def test_queued_suggestion_invalid_assignments(self, connection, client_id, experiment, assignments, expected_error):
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      connection.experiments(experiment.id).queued_suggestions().create(assignments=assignments)
    assert expected_error in str(e).lower()


class TestConditionalsSatisfiedAssignments(ExperimentsConditionalsTestBase):
  @pytest.fixture(
    params=[
      dict(x="10", a=1, b=-50, c="e"),
      dict(x="5", a=1, b=-50),
      dict(x="1", a=1),
      dict(x="10", a=1, b=-50, c="e"),
      dict(x="5", a=1, b=-50),
      dict(x="1", a=1),
    ]
  )
  def assignments(self, request):
    return request.param

  def test_suggestion_satisfied_assignments(self, connection, client_id, experiment, assignments):
    s = connection.experiments(experiment.id).suggestions().create(assignments=assignments)
    assert s.assignments.to_json() == assignments
    assert connection.experiments(experiment.id).observations().create(suggestion=s.id, values=[{"value": 0}])

  def test_create_observation_satisfied_assignments(self, connection, client_id, experiment, assignments):
    o = connection.experiments(experiment.id).observations().create(assignments=assignments, values=[{"value": 1}])
    assert o.assignments.to_json() == assignments

  def test_update_observation_satisfied_assignments(self, connection, client_id, experiment, assignments):
    s = connection.experiments(experiment.id).suggestions().create()
    o = connection.experiments(experiment.id).observations().create(suggestion=s.id, values=[{"value": 1}])
    o = (
      connection.experiments(experiment.id)
      .observations(o.id)
      .update(
        suggestion=None,
        assignments=assignments,
      )
    )
    assert o.assignments.to_json() == assignments

  def test_queued_suggestion_satisfied_assignments(self, connection, client_id, experiment, assignments):
    q = connection.experiments(experiment.id).queued_suggestions().create(assignments=assignments)
    assert q.assignments.to_json() == assignments


class TestConditionalsExhaustingLHC(ExperimentsConditionalsTestBase):
  def advance_past_lhc(self, services, connection, experiment):
    zigopt_experiment = services.experiment_service.find_by_id(experiment.id)
    stencil_length = get_low_discrepancy_stencil_length_from_experiment(zigopt_experiment)

    lhc_suggestions = []
    for v in range(stencil_length - 1):
      lhc_suggestions.append(connection.experiments(experiment.id).suggestions().create())
      connection.experiments(experiment.id).observations().create(
        suggestion=lhc_suggestions[-1].id,
        values=[{"value": v}],
        no_optimize=True,
      )
    lhc_suggestions.append(connection.experiments(experiment.id).suggestions().create())
    connection.experiments(experiment.id).observations().create(
      suggestion=lhc_suggestions[-1].id,
      values=[{"value": stencil_length - 1}],
      no_optimize=False,
    )

    return lhc_suggestions

  def test_consistent_lhc(self, services, connection, experiment):
    # Sometimes we fallback to random if this is not set.
    lhc_suggestions = self.advance_past_lhc(services, connection, experiment)
    zigopt_suggestions = services.suggestion_service.find_by_ids([s.id for s in lhc_suggestions])
    assert all(s.source == UnprocessedSuggestion.Source.LATIN_HYPERCUBE for s in zigopt_suggestions)

    new_suggestion = connection.experiments(experiment.id).suggestions().create()
    new_suggestion_source = services.suggestion_service.find_by_id(new_suggestion.id).source
    assert new_suggestion_source != UnprocessedSuggestion.Source.LATIN_HYPERCUBE

  @flaky(max_runs=3)
  def test_open_suggestions_lhc(self, services, connection, experiment):
    # Sometimes we fallback to random if this is not set.
    zigopt_experiment = services.experiment_service.find_by_id(experiment.id)
    stencil_length = get_low_discrepancy_stencil_length_from_experiment(zigopt_experiment)

    for v in range(stencil_length - 2):
      suggestion = connection.experiments(experiment.id).suggestions().create()
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        values=[{"value": v}],
        no_optimize=True,
      )

    suggestion = connection.experiments(experiment.id).suggestions().create()
    connection.experiments(experiment.id).observations().create(
      suggestion=suggestion.id,
      values=[{"value": stencil_length - 1}],
      no_optimize=False,
    )

    new_suggestion = connection.experiments(experiment.id).suggestions().create()
    new_suggestion_source = services.suggestion_service.find_by_id(new_suggestion.id).source
    assert new_suggestion_source == UnprocessedSuggestion.Source.LATIN_HYPERCUBE

    # Still return a LHC suggestion since there is an open suggestion with no parallel bandwidth set
    new_suggestion = connection.experiments(experiment.id).suggestions().create()
    new_suggestion_source = services.suggestion_service.find_by_id(new_suggestion.id).source
    assert new_suggestion_source == UnprocessedSuggestion.Source.LATIN_HYPERCUBE
