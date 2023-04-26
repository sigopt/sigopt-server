# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus
from typing import Any

import pytest

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestSuggestions(V1Base):
  """
    Test Suggestions
    """

  def test_create_suggestion(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      assert suggestion.state == "open"
      assert suggestion.experiment == experiment.id
      assert suggestion.created is not None
      assignments = suggestion.assignments
      for param in experiment.parameters:
        assignment = assignments.get(param.name)
        assert assignment is not None

  def test_create_custom_suggestion(self, connection):
    with connection.create_experiment(self.offline_categorical_experiment_meta) as experiment:
      suggestion = (
        connection.experiments(experiment.id)
        .suggestions()
        .create(
          assignments={
            "x": 1,
            "y": 2,
            "c": "b",
          }
        )
      )
      assert suggestion.state == "open"
      assert suggestion.experiment == experiment.id
      assert suggestion.created is not None
      assert suggestion.assignments.get("x") == 1
      assert suggestion.assignments.get("y") == 2
      assert suggestion.assignments.get("c") == "b"

  def test_invalid_create_custom(self, connection):
    with connection.create_experiment(self.offline_categorical_experiment_meta) as experiment:
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).suggestions().create(
          assignments={
            "x": 1,
          }
        )

      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).suggestions().create(
          assignments={
            "x": 1,
            "y": 2,
            "c": "b",
            "d": 3,
          }
        )

      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).suggestions().create(
          assignments={
            "x": "a",
            "y": 2,
            "c": "b",
            "d": 3,
          }
        )

      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).suggestions().create(task="not_multitask")

  def test_suggestion_state(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      assert suggestion.state == "open"
      suggestion = connection.experiments(experiment.id).suggestions(suggestion.id).fetch()
      assert suggestion.state == "open"
      connection.experiments(experiment.id).observations().create(suggestion=suggestion.id, values=[{"value": 0.0}])
      suggestion = connection.experiments(experiment.id).suggestions(suggestion.id).fetch()
      assert suggestion.state == "closed"

  def test_no_duplicate_suggestions(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      for _ in range(5):
        connection.experiments(experiment.id).observations().create(
          suggestion=suggestion.id,
          values=[{"value": 0.0}],
          no_optimize=True,
        )
      assert len(connection.experiments(experiment.id).suggestions().fetch().data) == 1

  def test_suggestion_filter(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      connection.experiments(experiment.id).suggestions().create()
      suggestions = connection.experiments(experiment.id).suggestions().fetch().data
      assert len(suggestions) == 2
      suggestions = connection.experiments(experiment.id).suggestions().fetch(state="open").data
      assert len(suggestions) == 2
      connection.experiments(experiment.id).observations().create(suggestion=suggestion.id, values=[{"value": 0.0}])
      suggestions = connection.experiments(experiment.id).suggestions().fetch().data
      assert len(suggestions) == 2
      suggestions = connection.experiments(experiment.id).suggestions().fetch(state="open").data
      assert len(suggestions) == 1
      ids = [suggestion.id]
      ids.append(connection.experiments(experiment.id).suggestions().create().id)
      suggestions = connection.experiments(experiment.id).suggestions().fetch(id=",".join(ids)).data
      assert len(suggestions) == 2
      assert sorted(ids) == sorted([s.id for s in suggestions])
      suggestions = connection.experiments(experiment.id).suggestions().fetch(id=suggestion.id).data
      assert len(suggestions) == 1
      assert suggestion.id == suggestions[0].id

  def test_suggestion_delete(self, connection):
    with connection.create_any_experiment() as experiment:
      for _ in range(6):
        connection.experiments(experiment.id).suggestions().create()
      suggestions = connection.experiments(experiment.id).suggestions().fetch().data
      assert len(suggestions) == 6

      connection.experiments(experiment.id).suggestions(suggestions[1].id).delete()
      suggestions = connection.experiments(experiment.id).suggestions().fetch().data
      assert len(suggestions) == 5
      connection.experiments(experiment.id).suggestions().delete()
      suggestions = connection.experiments(experiment.id).suggestions().fetch().data
      assert len(suggestions) == 0

  def test_suggestion_delete_by_state(self, connection):
    with connection.create_any_experiment() as experiment:
      connection.experiments(experiment.id).suggestions().create()
      suggestion = connection.experiments(experiment.id).suggestions().create()
      connection.experiments(experiment.id).observations().create(suggestion=suggestion.id, values=[{"value": 0.0}])
      connection.experiments(experiment.id).suggestions().delete(state="open")
      suggestions = connection.experiments(experiment.id).suggestions().fetch().data
      assert len(suggestions) == 1
      suggestions = connection.experiments(experiment.id).suggestions().fetch(state="open").data
      assert len(suggestions) == 0

  def test_invalid_suggestions_delete(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      connection.experiments(experiment.id).observations().create(
        suggestion=suggestion.id,
        values=[{"value": 0}],
        no_optimize=True,
      )
      connection.experiments(experiment.id).update(parameters=[{"name": "a", "bounds": {"max": 20, "min": 11}}])
      connection.experiments(experiment.id).suggestions().create()

  def test_suggestion_paging(self, connection):
    with connection.create_any_experiment() as experiment:
      expected_ids: list[str] = []
      limit = 2
      for _ in range(4 * limit):
        expected_ids.insert(0, connection.experiments(experiment.id).suggestions().create().id)
      partition = 2
      closed_ids, open_ids = expected_ids[:partition], expected_ids[partition:]
      for closed_id in closed_ids:
        connection.experiments(experiment.id).observations().create(
          suggestion=closed_id,
          values=[dict(value=0)],
        )

      ids = []
      suggestion_page = (
        connection.experiments(experiment.id)
        .suggestions()
        .fetch(
          limit=limit,
          state="open",
        )
      )
      ids.extend([s.id for s in suggestion_page.data])
      assert len(suggestion_page.data) == limit
      assert suggestion_page.paging.after is not None
      assert suggestion_page.paging.before is not None
      assert suggestion_page.count == 3 * limit
      suggestion_page = (
        connection.experiments(experiment.id)
        .suggestions()
        .fetch(
          limit=limit,
          before=suggestion_page.paging.before,
          state="open",
        )
      )
      ids.extend([s.id for s in suggestion_page.data])
      assert suggestion_page.paging.before is not None
      assert suggestion_page.paging.after is not None
      suggestion_page = (
        connection.experiments(experiment.id)
        .suggestions()
        .fetch(
          limit=limit,
          before=suggestion_page.paging.before,
          state="open",
        )
      )
      ids.extend([s.id for s in suggestion_page.data])
      assert suggestion_page.paging.before is None
      assert suggestion_page.paging.after is not None
      assert ids == open_ids

      ids = []
      suggestion_page = connection.experiments(experiment.id).suggestions().fetch(limit=limit)
      ids.extend([s.id for s in suggestion_page.data])
      assert len(suggestion_page.data) == limit
      assert suggestion_page.paging.after is not None
      assert suggestion_page.paging.before is not None
      assert suggestion_page.count == 4 * limit
      for _ in (0, 0):
        suggestion_page = (
          connection.experiments(experiment.id).suggestions().fetch(limit=limit, before=suggestion_page.paging.before)
        )
        ids.extend([s.id for s in suggestion_page.data])
        assert suggestion_page.paging.before is not None
        assert suggestion_page.paging.after is not None
      suggestion_page = (
        connection.experiments(experiment.id).suggestions().fetch(limit=limit, before=suggestion_page.paging.before)
      )
      ids.extend([s.id for s in suggestion_page.data])
      assert suggestion_page.paging.before is None
      assert suggestion_page.paging.after is not None
      assert ids == expected_ids

  def test_cross_url(self, connection):
    with connection.create_any_experiment() as e1:
      with connection.create_any_experiment() as e2:
        suggestion = connection.experiments(e1.id).suggestions().create()

        with RaisesApiException(HTTPStatus.NOT_FOUND):
          connection.experiments(e2.id).suggestions(suggestion.id).fetch()
        connection.experiments(e1.id).suggestions(suggestion.id).fetch()

        with RaisesApiException(HTTPStatus.NOT_FOUND):
          connection.experiments(e2.id).suggestions(suggestion.id).update(metadata={})
        connection.experiments(e1.id).suggestions(suggestion.id).update(metadata={})

        with RaisesApiException(HTTPStatus.NOT_FOUND):
          connection.experiments(e2.id).suggestions(suggestion.id).delete()
        connection.experiments(e1.id).suggestions(suggestion.id).delete()


class TestSuggestionMetadata(V1Base):
  def test_create_with_metadata(self, connection):
    with connection.create_any_experiment() as experiment:
      metadata = {"foo": "bar"}
      suggestion = connection.experiments(experiment.id).suggestions().create(metadata=metadata)
      assert suggestion.metadata.to_json() == metadata
      suggestion = connection.experiments(experiment.id).suggestions(suggestion.id).fetch()
      assert suggestion.metadata.to_json() == metadata

  def test_create_with_invalid_metadata(self, connection):
    metadata: Any

    with connection.create_any_experiment() as experiment:
      metadata = ["foo", "bar"]
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).suggestions().create(metadata=metadata)

      metadata = {"baz": ["foo", "bar"]}
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).suggestions().create(metadata=metadata)

  def test_create_with_long_metadata(self, connection):
    with connection.create_any_experiment() as experiment:
      metadata = {x: x for x in range(500)}
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).suggestions().create(metadata=metadata)

  def test_update_metadata(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      # set metadata
      metadata = {"foo": "bar"}
      suggestion = connection.experiments(experiment.id).suggestions(suggestion.id).update(metadata=metadata)
      assert suggestion.metadata.to_json() == metadata
      # change metadata
      metadata = {"biz": "baz"}
      suggestion = connection.experiments(experiment.id).suggestions(suggestion.id).update(metadata=metadata)
      assert suggestion.metadata.to_json() == metadata
      # update with no effect
      suggestion = connection.experiments(experiment.id).suggestions(suggestion.id).update()
      assert suggestion.metadata.to_json() == metadata
      # unset metadata
      suggestion = connection.experiments(experiment.id).suggestions(suggestion.id).update(metadata=None)
      assert suggestion.metadata is None


class TestConnectedObservations(V1Base):
  def test_delete_observation(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      observation = (
        connection.experiments(experiment.id).observations().create(suggestion=suggestion.id, values=[{"value": 0.0}])
      )
      connection.experiments(experiment.id).observations(observation.id).delete()
      assert connection.experiments(experiment.id).suggestions().fetch(state="open").count == 0
      suggestion_page = connection.experiments(experiment.id).suggestions().fetch()
      assert suggestion_page.count == 1
      closed_suggestion = suggestion_page.data[0]
      assert closed_suggestion.state == "closed"
      assert closed_suggestion.id == suggestion.id


class TestSuggestionsListDetail(V1Base):
  @pytest.mark.parametrize(
    "detail_kwargs,expected_count",
    [
      (dict(), 2),
      (dict(state="open"), 1),
      (dict(deleted=False), 2),
      (dict(deleted=False, state="open"), 1),
      (dict(deleted=True), 2),
      (dict(deleted=True, state="open"), 1),
    ],
  )
  def test_list_detail(self, connection, detail_kwargs, expected_count):
    with connection.create_any_experiment() as e:
      suggestion = connection.experiments(e.id).suggestions().create()
      connection.experiments(e.id).observations().create(suggestion=suggestion.id, values=[{"value": 0.0}])

      suggestion = connection.experiments(e.id).suggestions().create()
      connection.experiments(e.id).observations().create(suggestion=suggestion.id, values=[{"value": 0.0}])
      connection.experiments(e.id).suggestions(suggestion.id).delete()

      suggestion = connection.experiments(e.id).suggestions().create()

      suggestion = connection.experiments(e.id).suggestions().create()
      connection.experiments(e.id).suggestions(suggestion.id).delete()

      suggestions_page = connection.experiments(e.id).suggestions().fetch(**detail_kwargs)
      assert len(suggestions_page.data) == suggestions_page.count
      assert suggestions_page.count == expected_count
