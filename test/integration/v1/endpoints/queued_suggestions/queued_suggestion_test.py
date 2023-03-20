# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestCreateQueuedSuggestions(V1Base):
  def test_create_queued_suggestion(self, connection):
    a = dict(x=1, y=2, c="b")
    with connection.create_experiment(self.offline_categorical_experiment_meta) as experiment:
      queued_suggestion = connection.experiments(experiment.id).queued_suggestions().create(assignments=a)
      assert queued_suggestion.id is not None
      assert queued_suggestion.experiment == experiment.id
      assert queued_suggestion.assignments.to_json() == a

  def test_invalid_create_custom(self, connection):
    with connection.create_experiment(self.offline_categorical_experiment_meta) as experiment:
      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).queued_suggestions().create()

      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).queued_suggestions().create(assignments=dict(x=1))

      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).queued_suggestions().create(assignments=dict(x=1, y=2, c="b", d=3))

      with RaisesApiException(HTTPStatus.BAD_REQUEST):
        connection.experiments(experiment.id).queued_suggestions().create(assignments=dict(x="a", y=2, c="b", d=3))


class TestDetailQueuedSuggestions(V1Base):
  def test_detail_queued_suggestion(self, connection):
    a = dict(x=1, y=2, c="b")
    with connection.create_experiment(self.offline_categorical_experiment_meta) as experiment:
      queued_suggestion = connection.experiments(experiment.id).queued_suggestions().create(assignments=a)
      queued_id = queued_suggestion.id
      queued_suggestion_detail = connection.experiments(experiment.id).queued_suggestions(queued_id).fetch()
      assert queued_suggestion == queued_suggestion_detail

  def test_detail_multiple_queued_suggestions(self, connection):
    with connection.create_experiment(self.offline_categorical_experiment_meta) as experiment:
      connection.experiments(experiment.id).queued_suggestions().create(assignments=dict(x=1, y=2, c="a"))
      connection.experiments(experiment.id).queued_suggestions().create(assignments=dict(x=1, y=2, c="b"))
      connection.experiments(experiment.id).queued_suggestions().create(assignments=dict(x=1, y=2, c="c"))
      pagination = connection.experiments(experiment.id).queued_suggestions().fetch()
      assert pagination.count == 3


class TestDeleteQueuedSuggestions(V1Base):
  def test_delete_removes_from_queue(self, connection):
    a = dict(x=1, y=2, c="b")
    b = dict(x=0, y=0, c="a")
    with connection.create_experiment(self.offline_categorical_experiment_meta) as experiment:
      q = connection.experiments(experiment.id).queued_suggestions().create(assignments=a)
      connection.experiments(experiment.id).queued_suggestions().create(assignments=b)
      connection.experiments(experiment.id).queued_suggestions(q.id).delete()
      suggestion = connection.experiments(experiment.id).suggestions().create()
      assert suggestion.assignments.to_json() == b


class TestCreateSuggestions(V1Base):
  def test_create_suggestion(self, connection):
    a = dict(x=1, y=2, c="b")
    with connection.create_experiment(self.offline_categorical_experiment_meta) as experiment:
      queued_suggestion = connection.experiments(experiment.id).queued_suggestions().create(assignments=a)
      suggestion = connection.experiments(experiment.id).suggestions().create()
      assert suggestion.assignments.to_json() == a

      pagination = connection.experiments(experiment.id).queued_suggestions().fetch()
      assert pagination.count == 0
      assert queued_suggestion.id not in [q.id for q in pagination.data]

      suggestion = connection.experiments(experiment.id).suggestions().create()
      assert suggestion.assignments.to_json() != a

  def test_create_multiple_suggestions(self, connection):
    a = dict(x=1, y=2, c="b")
    b = dict(x=0, y=0, c="a")
    with connection.create_experiment(self.offline_categorical_experiment_meta) as experiment:
      connection.experiments(experiment.id).queued_suggestions().create(assignments=a)
      connection.experiments(experiment.id).queued_suggestions().create(assignments=b)
      suggestion = connection.experiments(experiment.id).suggestions().create()
      assert suggestion.assignments.to_json() == a
      suggestion = connection.experiments(experiment.id).suggestions().create()
      assert suggestion.assignments.to_json() == b

  def test_queued_can_be_duplicate_suggestion(self, connection):
    with connection.create_experiment(self.offline_categorical_experiment_meta) as experiment:
      s1 = connection.experiments(experiment.id).suggestions().create()
      assignments = s1.assignments
      connection.experiments(experiment.id).observations().create(suggestion=s1.id, values=[{"value": 1}])
      connection.experiments(experiment.id).queued_suggestions().create(assignments=assignments)
      s2 = connection.experiments(experiment.id).suggestions().create()
      assert s1.assignments.to_json() == s2.assignments.to_json()
