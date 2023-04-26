# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.protobuf.lib import copy_protobuf
from zigopt.protobuf.proxy import Proxy


class BaseHasMeasurementsProxy(Proxy):
  def get_all_measurements(self, experiment):
    measurements = self.sorted_measurements()
    if len(measurements) == 1 and not experiment.has_multiple_metrics:
      only_measurement = copy_protobuf(measurements[0])
      if experiment.all_metrics[0].HasField("name"):
        only_measurement.name = experiment.all_metrics[0].name
      measurements = [(only_measurement)]
    return measurements

  def get_all_measurements_for_maximization(self, experiment):
    all_measurements = [copy_protobuf(v) for v in self.get_all_measurements(experiment)]
    for i, metric in enumerate(experiment.all_metrics):
      if metric.is_minimized:
        all_measurements[i].value = -all_measurements[i].value
    return all_measurements

  def get_optimized_measurements_for_maximization(self, experiment):
    all_measurements_for_maximization = self.get_all_measurements_for_maximization(experiment)
    optimized_metric_names = {metric.name for metric in experiment.optimized_metrics}
    return [m for m in all_measurements_for_maximization if m.name in optimized_metric_names]

  def value_for_maximization(self, experiment, name):
    value = find(self.get_all_measurements_for_maximization(experiment), lambda v: v.name == name)
    if value and value.HasField("value"):
      return value.value
    return None

  def metric_value(self, experiment, name):
    measurement = find(self.get_all_measurements(experiment), lambda v: v.name == name)
    if measurement and measurement.HasField("value"):
      return measurement.value
    return None

  def metric_value_var(self, experiment, name):
    measurement = find(self.get_all_measurements(experiment), lambda v: v.name == name)
    if measurement and measurement.HasField("value_var"):
      return measurement.value_var
    return None

  def _sorted_attributes(self, experiment, attr):
    measurements = self.get_all_measurements(experiment)
    num_expected_metrics = len(experiment.all_metrics)
    assert self.reported_failure or len(measurements) == num_expected_metrics

    attr_fields = [getattr(m, attr) if m.HasField(attr) else None for m in measurements]
    if not attr_fields or any(f is None for f in attr_fields):
      return None
    return attr_fields

  def sorted_all_metric_values(self, experiment):
    return self._sorted_attributes(experiment, "value")

  def sorted_all_metric_value_vars(self, experiment):
    return self._sorted_attributes(experiment, "value_var")

  def sorted_measurements(self):
    raise NotImplementedError()
