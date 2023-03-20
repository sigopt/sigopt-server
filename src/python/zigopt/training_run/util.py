# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import math

from zigopt.common import generator_to_list


def get_observation_values_dict_from_training_run(experiment, training_run):
  return get_observation_values_dict_from_training_run_values_map(experiment, training_run.training_run_data.values_map)


# NOTE: in case `values_map` doesn't exist, this will return an empty list which the caller
# might want to handle
@generator_to_list
def get_observation_values_dict_from_training_run_values_map(experiment, values_map):
  values_map = dict(values_map)
  for metric in experiment.all_metrics:
    if metric.name in values_map:
      v = values_map[metric.name]
      yield {"name": metric.name, "value": v.value, "value_stddev": math.sqrt(v.value_var)}
