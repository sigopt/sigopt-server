# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import csv
import io

from zigopt.common import *

from integration.utils.make_values import make_values
from integration.web.experiment.test_base import ExperimentWebBase


class TestExperiment(ExperimentWebBase):
  def get_sample_values(self, value, e, value_stddev=None):
    return [
      {
        "name": metric.name,
        "value": value,
        "value_stddev": value_stddev,
      }
      for metric in e.metrics
    ]

  def get_sample_observations(self, api_connection, e):
    o1 = (
      api_connection.experiments(e.id)
      .observations()
      .create(
        assignments={"a": 5, "b": 5.001, "c": "e"},
        values=self.get_sample_values(3.33, e),
        failed=None,
        no_optimize=True,
      )
    )
    o2 = (
      api_connection.experiments(e.id)
      .observations()
      .create(
        assignments={"a": 9, "b": 9.333, "c": "d"},
        values=self.get_sample_values(0.999, e, 0.1),
        failed=False,
        metadata={"a": "b", "host": "127.0.0.1"},
        no_optimize=True,
      )
    )
    o3 = (
      api_connection.experiments(e.id)
      .observations()
      .create(
        assignments={"a": 7, "b": 7.77, "c": "d"},
        failed=True,
        no_optimize=True,
      )
    )
    o4 = (
      api_connection.experiments(e.id)
      .observations()
      .create(
        assignments={"a": 0, "b": 0, "c": "d"},
        values=self.get_sample_values(0, e, 0),
        metadata={"a": "c", "number": 0},
        no_optimize=True,
      )
    )
    return (o4, o3, o2, o1)

  def get_csv_file(self, logged_in_web_connection, e):
    return logged_in_web_connection.get(f"/experiment/{e.id}/historydownload").response_text()

  def test_csv_download(self, api_connection, logged_in_web_connection, meta):
    with api_connection.create_experiment(meta) as e:
      s = api_connection.experiments(e.id).suggestions().create()
      api_connection.experiments(e.id).observations().create(suggestion=s.id, values=make_values(e))
      csv_lines = list(csv.reader(io.StringIO(self.get_csv_file(logged_in_web_connection, e))))
      assert len(csv_lines) == 2

  def test_csv_download_format(self, api_connection, logged_in_web_connection):
    with api_connection.create_experiment(
      {
        "parameters": [
          {"name": "a", "type": "int", "bounds": {"min": 0, "max": 50}},
          {"name": "b", "type": "double", "bounds": {"min": 0, "max": 10}},
          {"name": "c", "type": "categorical", "categorical_values": [{"name": "d"}, {"name": "e"}]},
        ],
      }
    ) as e:

      def assert_equal_even_if_none(csv_value, observation_value):
        if is_boolean(observation_value):
          assert csv_value == ("true" if observation_value else "false")
        elif is_number(observation_value):
          assert float(csv_value) == observation_value
        elif observation_value is not None:
          assert csv_value == str(observation_value)
        else:
          assert csv_value == ""

      observations = self.get_sample_observations(api_connection, e)
      reader = csv.reader(io.StringIO(self.get_csv_file(logged_in_web_connection, e)))
      title_line = next(reader)
      assert set(title_line) == set(
        [
          "parameter-a",
          "parameter-b",
          "parameter-c",
          "failed",
          "created",
          "metadata-a",
          "metadata-host",
          "metadata-number",
          "id",
        ]
        + flatten(
          [f"value-{m.name}" if m.name else "value", f"value_stddev-{m.name}" if m.name else "value_stddev"]
          for m in e.metrics
        )
        + (["task_name"] if e.tasks else [])
      )

      task_names = [t.name for t in e.tasks] if e.tasks else []
      for line, observation in zip(reader, observations):
        assert int(line[0]) == int(observation.assignments["a"])
        assert float(line[1]) == float(observation.assignments["b"])
        assert line[2] == str(observation.assignments["c"])
        for i, metric in enumerate(e.metrics, start=2):
          # pylint: disable=cell-var-from-loop
          matching_value = find(observation.values, lambda v: v.name == metric.name)
          # pylint: enable=cell-var-from-loop
          assert_equal_even_if_none(line[2 * i - 1], matching_value and matching_value.value)
          assert_equal_even_if_none(line[2 * i], matching_value and matching_value.value_stddev)
        if task_names:
          assert line[-7] in task_names
        assert_equal_even_if_none(line[-6], observation.failed)
        assert_equal_even_if_none(line[-5], observation.created)
        assert_equal_even_if_none(line[-4], (observation.metadata or {}).get("a"))
        assert_equal_even_if_none(line[-3], (observation.metadata or {}).get("host"))
        assert_equal_even_if_none(line[-2], (observation.metadata or {}).get("number"))
        assert line[-1] == observation.id

  def test_csv_injection(self, api_connection, logged_in_web_connection, meta):
    with api_connection.create_experiment(meta) as e:
      s = api_connection.experiments(e.id).suggestions().create()
      api_connection.experiments(e.id).observations().create(
        metadata={"x": "=cmd|'/C notepad'!'A1'"},
        suggestion=s.id,
        values=make_values(e),
      )
      csv_lines = list(csv.reader(io.StringIO(self.get_csv_file(logged_in_web_connection, e))))
      for line in csv_lines:
        for element in line:
          assert not element.startswith("=")
