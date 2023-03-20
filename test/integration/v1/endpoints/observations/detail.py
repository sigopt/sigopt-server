# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.api.paging import serialize_paging_marker
from zigopt.protobuf.gen.api.paging_pb2 import PagingMarker, PagingSymbol

from integration.v1.test_base import V1Base


class TestDetailObservations(V1Base):
  """
    Test Detailing Observations
    """

  def test_detail_observation(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      observation = (
        connection.experiments(experiment.id)
        .observations()
        .create(
          values=[{"value": 5.1}],
          assignments=suggestion.assignments,
        )
      )
      observation_detail = connection.experiments(experiment.id).observations(observation.id).fetch()
      assert observation_detail.assignments == suggestion.assignments
      assert observation_detail.id == observation.id
      assert observation_detail.value == observation.value
      assert observation_detail.value_stddev is None

  def test_detail_multiple_observations(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      created_observations = []
      for i in range(5):
        created_observations.append(
          connection.experiments(experiment.id)
          .observations()
          .create(
            values=[{"value": -i}],
            assignments=suggestion.assignments,
            no_optimize=True,
          )
        )
      observations = connection.experiments(experiment.id).observations().fetch().data
      assert len(observations) == 5
      assert [o.id for o in observations] == list(reversed([o.id for o in created_observations]))
      observations = connection.experiments(experiment.id).observations().fetch(sort="value").data
      assert len(observations) == 5
      assert [o.id for o in observations] == [o.id for o in created_observations]

      def marker(s1, s2):
        return serialize_paging_marker(PagingMarker(symbols=[s1, s2]))

      null_value_marker = marker(PagingSymbol(null_value=PagingSymbol.NULL_VALUE), PagingSymbol(int_value=0))
      data = connection.experiments(experiment.id).observations().fetch(sort="value", before=null_value_marker).data
      assert len(data) == 5
      data = connection.experiments(experiment.id).observations().fetch(sort="value", after=null_value_marker).data
      assert len(data) == 0
      real_value_marker = marker(PagingSymbol(double_value=-6.0), PagingSymbol(int_value=0))
      data = connection.experiments(experiment.id).observations().fetch(sort="value", before=real_value_marker).data
      assert len(data) == 0
      data = connection.experiments(experiment.id).observations().fetch(sort="value", after=real_value_marker).data
      assert len(data) == 5

  @pytest.mark.parametrize(
    "observation_field,sort_key",
    [
      (lambda o: int(o.id), "id"),
      (lambda o: o.values[0].value, "value-metric1"),
      (lambda o: o.values[0].value_stddev, "value_stddev-metric1"),
      (lambda o: o.values[1].value, "value-metric2"),
      (lambda o: o.values[1].value_stddev, "value_stddev-metric2"),
      (lambda o: o.assignments["parameter1"], "parameter-parameter1"),
    ],
  )
  def test_sort_params(self, connection, observation_field, sort_key):
    with connection.create_any_experiment(
      metrics=[{"name": "metric1"}, {"name": "metric2"}],
      observation_budget=5,
      parameters=[
        {
          "name": "parameter1",
          "type": "double",
          "bounds": {"min": 0, "max": 1},
        }
      ],
    ) as experiment:
      created_observations = [
        connection.experiments(experiment.id)
        .observations()
        .create(
          values=[
            {"name": "metric1", "value": -i, "value_stddev": i + 1},
            {"name": "metric2", "value": i, "value_stddev": 5 - i},
          ],
          assignments={"parameter1": i / 5},
          no_optimize=True,
        )
        for i in range(5)
      ]

      observations = connection.experiments(experiment.id).observations().fetch(ascending=False, sort=sort_key).data
      assert len(observations) == 5
      sorted_observations = sorted(created_observations, key=lambda o: -observation_field(o))
      assert [o.id for o in observations] == [o.id for o in sorted_observations]

      observations = connection.experiments(experiment.id).observations().fetch(ascending=True, sort=sort_key).data
      assert len(observations) == 5
      sorted_observations = sorted(created_observations, key=observation_field)
      assert [o.id for o in observations] == [o.id for o in sorted_observations]

  def test_with_deleted_clause(self, connection):
    with connection.create_any_experiment() as experiment:
      suggestion = connection.experiments(experiment.id).suggestions().create()
      created_observations = []
      for i in range(5):
        created_observations.insert(
          0,
          connection.experiments(experiment.id)
          .observations()
          .create(
            values=[{"value": -i}],
            assignments=suggestion.assignments,
            no_optimize=True,
          ),
        )

      observations_page = connection.experiments(experiment.id).observations().fetch(deleted=True)
      assert observations_page.count == len(observations_page.data) == 0

      observations_page = connection.experiments(experiment.id).observations().fetch(deleted=False)
      assert observations_page.count == len(observations_page.data) == 5
      assert [o.id for o in observations_page.data] == [o.id for o in created_observations]

      connection.experiments(experiment.id).observations(created_observations[-1].id).delete()
      connection.experiments(experiment.id).observations(created_observations[0].id).delete()

      observations_page = connection.experiments(experiment.id).observations().fetch(deleted=True)
      assert observations_page.count == len(observations_page.data) == 2
      assert [o.id for o in observations_page.data] == [created_observations[0].id, created_observations[-1].id]

      observations_page = connection.experiments(experiment.id).observations().fetch(deleted=False)
      assert observations_page.count == len(observations_page.data) == 3
      assert [o.id for o in observations_page.data] == [o.id for o in created_observations][1:-1]
