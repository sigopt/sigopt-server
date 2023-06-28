# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestDeleteObservations(V1Base):
  """
    Test Deleting Observations
    """

  def test_delete_observation(self, connection):
    experiment = connection.create_any_experiment()
    suggestion = connection.experiments(experiment.id).suggestions().create()
    observation = (
      connection.experiments(experiment.id)
      .observations()
      .create(
        values=[{"value": 5.1}],
        assignments=suggestion.assignments,
        no_optimize=True,
      )
    )
    connection.experiments(experiment.id).observations().create(
      values=[{"value": 2.6}],
      assignments=suggestion.assignments,
      no_optimize=True,
    )
    connection.experiments(experiment.id).observations(observation.id).delete(no_optimize=True)
    observations = connection.experiments(experiment.id).observations().fetch().data
    assert len(observations) == 1

  def test_delete_all_observations(self, connection):
    experiment = connection.create_any_experiment()
    suggestion = connection.experiments(experiment.id).suggestions().create()
    for i in range(3):
      connection.experiments(experiment.id).observations().create(
        values=[{"value": i}],
        assignments=suggestion.assignments,
        no_optimize=True,
      )
    connection.experiments(experiment.id).observations().delete()
    observations = connection.experiments(experiment.id).observations().fetch().data
    assert len(observations) == 0

  def test_cross_url(self, connection):
    e1 = connection.create_any_experiment()
    e2 = connection.create_any_experiment()
    suggestion = connection.experiments(e1.id).suggestions().create()
    observation = connection.experiments(e1.id).observations().create(suggestion=suggestion.id, values=[{"value": 2.6}])

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.experiments(e2.id).observations(observation.id).fetch()
    connection.experiments(e1.id).observations(observation.id).fetch()

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.experiments(e2.id).observations(observation.id).update(**dict(metadata={}))
    connection.experiments(e1.id).observations(observation.id).update(**dict(metadata={}))

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.experiments(e2.id).observations(observation.id).delete()
    connection.experiments(e1.id).observations(observation.id).delete()
