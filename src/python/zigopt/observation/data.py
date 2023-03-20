# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.common.numbers import *
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.net.errors import BadParamError
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationValue


def value_var_from_json(json_dict, experiment, default=None):
  if "value_stddev" in json_dict:
    value_stddev = get_opt_with_validation(json_dict, "value_stddev", ValidationType.number)
    return None if value_stddev is None else value_stddev * value_stddev
  elif "value_var" in json_dict:
    return get_opt_with_validation(json_dict, "value_var", ValidationType.number)
  else:
    return default


def value_from_json(json_dict, default=None):
  if "value" not in json_dict:
    return default
  return get_opt_with_validation(json_dict, "value", ValidationType.number)


def validate_metric_names(values, experiment):
  name_counts = distinct_counts([v.get("name") for v in values])
  for name, count in name_counts.items():
    if count >= 2:
      raise BadParamError(f"Duplicate name: {name}")

  names = list(name_counts.keys())
  non_empty_names = compact(names)
  if len(names) >= 2 and len(names) > len(non_empty_names):
    raise BadParamError("A name must be specified for all values.")

  if experiment is not None:
    experiment_metrics = set(m.name for m in experiment.all_metrics)
    if not experiment_metrics and non_empty_names:
      raise BadParamError(
        "value names should match experiment metric names. Names should not be specified for unnamed metrics."
      )
    # NOTE: allow legacy of submitting unnamed metrics, whether or not experiment-metric name exists
    elif len(names) == 1 and len(non_empty_names) == 0 and len(experiment_metrics) <= 1:
      pass
    elif experiment_metrics and not experiment_metrics.issubset(names):
      raise BadParamError(f"values must have metric names defined in experiment: {experiment_metrics}")


@generator_to_list
def get_formatted_values(values, experiment, experiment_metrics, old_values=None):
  # The number of experiment metrics doesn't equal the number of observation values OR
  # the experiment has no metric, which means that the experiment is not multicriteria and the
  # metric is unnamed (so the observation should only have one, also unnamed, value)
  if (experiment_metrics and len(experiment_metrics) != len(values)) or not experiment_metrics and len(values) != 1:
    if experiment.has_user_defined_metric:
      raise BadParamError("The number of observation values and experiment metrics must be equal.")
    else:
      raise BadParamError("Experiments without a defined `metrics` do not support multiple values.")
  validate_metric_names(values, experiment)
  old_values_by_name = to_map_by_key(coalesce(old_values, []), key=lambda v: v.name)
  for v in values:
    assert is_mapping(v)
    name = get_opt_with_validation(v, "name", ValidationType.string)
    old_v = old_values_by_name.get(coalesce(name, ""))
    if old_values_by_name and old_v is None:
      raise BadParamError(f"Invalid metric name {name}")

    val = value_from_json(v, default=napply(old_v, lambda v: v.GetFieldOrNone("value")))
    v_var = value_var_from_json(v, experiment, default=napply(old_v, lambda v: v.GetFieldOrNone("value_var")))

    if val is None:
      raise BadParamError(
        f"Missing value for: {name}" if name else "A value should be specified for all entries in the 'values' list."
      )

    observation_value = ObservationValue(name=name if name else None)
    _set_observation_value(observation_value, val, v_var)
    yield observation_value


def create_observation_data(observation_data, values, observation, experiment, failed):
  observation_data.reported_failure = coalesce(failed, False)
  if not observation_data.reported_failure:
    experiment_metrics = [m.name for m in experiment.all_metrics]
    if values is not None:
      values_list = get_formatted_values(values, experiment, experiment_metrics, old_values=None)
      observation_data.values.extend(values_list)


def update_observation_data(observation_data, values, observation, experiment, failed):
  observation_data.reported_failure = coalesce(failed, False)
  if observation_data.reported_failure:
    if observation_data.values:
      for v in observation_data.values:
        v.ClearField("value")
        v.ClearField("value_var")
    return

  experiment_metrics = [m.name for m in experiment.all_metrics]
  if values is not None:
    values_list = get_formatted_values(
      values,
      experiment,
      experiment_metrics,
      old_values=observation_data.values,
    )
    del observation_data.values[:]
    observation_data.values.extend(values_list)


def _set_observation_value(observation_value, value, value_var):
  """
    Updates observations with the multiple 'values' field
    """
  if is_nan(value):
    value = None
  if is_nan(value_var):
    value_var = None
  if value is not None:
    observation_value.value = float(value)
  else:
    observation_value.ClearField("value")
  if observation_value.value is not None and value_var is not None:
    observation_value.value_var = float(value_var)
  else:
    observation_value.ClearField("value_var")
