# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.experiment.constant import (
  ALL_PARAMETER_PRIOR_NAMES,
  EXPERIMENT_PARAMETER_NAME_TO_TYPE,
  PARAMETER_PRIOR_NAME_TO_TYPE,
  PARAMETER_TRANSFORMATION_NAME_TO_TYPE,
)
from zigopt.experiment.model import ExperimentMetaProxy, ExperimentParameterProxy
from zigopt.handlers.validate.assignments import get_assignment
from zigopt.handlers.validate.experiment import validate_categorical_value, validate_parameter_name
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.net.errors import BadParamError, InvalidKeyError, InvalidValueError
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  PARAMETER_CATEGORICAL,
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  ExperimentMeta,
  ExperimentParameter,
)
from zigopt.sigoptcompute.constant import MINIMUM_DOMAIN_EDGE_LENGTH

from sigoptaux.constant import ParameterPriorNames


class GridError(BadParamError):
  def __init__(self, parameter, msg):
    grid_error_prefix = f"`grid` provided for parameter {parameter.name} is invalid. "
    super().__init__(grid_error_prefix + msg)


def set_experiment_parameter_list_from_json(experiment_meta, experiment_json, user_facing_class_name="Experiment"):
  conditionals_map = ExperimentMetaProxy(experiment_meta).conditionals_map

  parameters_json = get_opt_with_validation(
    experiment_json,
    "parameters",
    ValidationType.arrayOf(ValidationType.object),
  )

  if not parameters_json:
    raise BadParamError(f"{user_facing_class_name}s must have at least one parameter.")

  seen_names = set()
  for parameter_json in parameters_json:
    parameter = experiment_meta.all_parameters_unsorted.add()
    set_experiment_parameter_from_json(parameter, parameter_json, experiment_meta.experiment_type, conditionals_map)
    if parameter.name in seen_names:
      raise InvalidValueError(f"Duplicate parameter name: {parameter.name}")
    elif parameter.name in conditionals_map:
      raise InvalidValueError(f"Cannot have parameter and conditional both named {parameter.name}")
    seen_names.add(parameter.name)


def set_experiment_parameter_from_json(parameter, parameter_json, experiment_type, conditionals_map):
  set_parameter_name_from_json(parameter, parameter_json)
  set_parameter_type_from_json(parameter, parameter_json)
  set_transformation_from_json(parameter, parameter_json)
  set_bounds_from_json(parameter, parameter_json, experiment_type)
  set_prior_from_json(parameter, parameter_json)
  set_categorical_values_from_json(parameter, parameter_json)

  if "grid" in parameter_json or experiment_type == ExperimentMeta.GRID:
    set_grid_values_from_json(parameter, parameter_json)

  set_default_value_from_json(parameter, parameter_json)
  set_parameter_conditions_from_json(parameter, parameter_json, conditionals_map)


def set_parameter_name_from_json(parameter, parameter_json):
  parameter.name = validate_parameter_name(get_with_validation(parameter_json, "name", ValidationType.string))


def set_parameter_type_from_json(parameter, parameter_json):
  param_type_string = get_with_validation(parameter_json, "type", ValidationType.string)
  try:
    parameter.param_type = EXPERIMENT_PARAMETER_NAME_TO_TYPE[param_type_string]
  except KeyError as e:
    raise InvalidValueError(
      f"Invalid param_type: {param_type_string} must be one of {list(EXPERIMENT_PARAMETER_NAME_TO_TYPE.keys())}"
    ) from e


def set_bounds_from_json(parameter, parameter_json, experiment_type):
  grid_values = get_opt_with_validation(parameter_json, "grid", ValidationType.arrayOf(ValidationType.number))
  if grid_values:
    if parameter_json.get("bounds") is not None:
      raise InvalidKeyError(
        "Parameters with grid cannot have bounds on parameters. They are inferred from the supplied grid."
      )

  if parameter.param_type not in [PARAMETER_INT, PARAMETER_DOUBLE]:
    if parameter_json.get("bounds") is not None:
      raise InvalidKeyError("bounds", msg=f"Categorical parameter {parameter.name} cannot have `bounds`")
    return

  bounds_json = get_opt_with_validation(parameter_json, "bounds", ValidationType.object)
  validation_type = ValidationType.integer if parameter.param_type == PARAMETER_INT else ValidationType.number

  if not (bounds_json or grid_values):
    raise InvalidKeyError("bounds", msg=f"Parameter {parameter.name} must have `bounds`")

  # TODO(SN-1118): better error messages
  if grid_values:
    parameter.bounds.minimum = min(grid_values)
    parameter.bounds.maximum = max(grid_values)
  else:
    parameter.bounds.minimum = get_with_validation(bounds_json, "min", validation_type)
    parameter.bounds.maximum = get_with_validation(bounds_json, "max", validation_type)

  if parameter.bounds.maximum < parameter.bounds.minimum:
    raise BadParamError("Invalid bounds: max must be greater than min")
  elif parameter.bounds.maximum - parameter.bounds.minimum < MINIMUM_DOMAIN_EDGE_LENGTH:
    raise BadParamError(
      f"Invalid bounds: {parameter.bounds} does not exceed min length: {MINIMUM_DOMAIN_EDGE_LENGTH}",
    )

  if parameter.transformation == ExperimentParameter.TRANSFORMATION_LOG:
    if parameter.bounds.minimum <= 0.0:
      raise BadParamError("Invalid bounds for log-transformation: bounds must be positive")


def set_prior_from_json(parameter, parameter_json):
  if parameter.param_type != PARAMETER_DOUBLE:
    if parameter_json.get("prior") is not None:
      raise InvalidKeyError("Currently only continuous parameters can have `prior`")
    return
  if parameter.transformation == ExperimentParameter.TRANSFORMATION_LOG:
    if parameter_json.get("prior") is not None:
      raise InvalidKeyError("Currently, parameters with a log transformation cannot have priors")

  if parameter_json.get("prior") is None:
    return

  if parameter_json.get("grid") is not None:
    raise GridError(parameter, "Grid parameters cannot have priors.")

  prior_json = get_with_validation(parameter_json, "prior", ValidationType.object)
  prior_name = get_with_validation(prior_json, "name", ValidationType.string)
  if prior_name not in ALL_PARAMETER_PRIOR_NAMES:
    raise InvalidValueError(f"Invalid prior type: {prior_name} must be one of {ALL_PARAMETER_PRIOR_NAMES}.")

  parameter.prior.prior_type = PARAMETER_PRIOR_NAME_TO_TYPE[prior_name]
  if prior_name == ParameterPriorNames.NORMAL:
    parameter.prior.normal_prior.mean = get_with_validation(prior_json, "mean", ValidationType.number)
    if (
      parameter.prior.normal_prior.mean > parameter.bounds.maximum
      or parameter.prior.normal_prior.mean < parameter.bounds.minimum
    ):
      raise BadParamError("`mean` must be within the bounds of the parameter.")
    parameter.prior.normal_prior.scale = get_with_validation(prior_json, "scale", ValidationType.number)
    if parameter.prior.normal_prior.scale <= 0:
      raise BadParamError("`scale` must be positive.")
  elif prior_name == ParameterPriorNames.BETA:
    parameter.prior.beta_prior.shape_a = get_with_validation(prior_json, "shape_a", ValidationType.number)
    parameter.prior.beta_prior.shape_b = get_with_validation(prior_json, "shape_b", ValidationType.number)
    if parameter.prior.beta_prior.shape_a <= 0 or parameter.prior.beta_prior.shape_b <= 0:
      raise BadParamError(f"shape parameters for {ParameterPriorNames.BETA} must be positive.")
  else:
    raise InvalidValueError(f"{prior_name} prior is not supported currently.")


def set_categorical_values_from_json(parameter, parameter_json):
  if parameter.param_type != PARAMETER_CATEGORICAL:
    if parameter_json.get("categorical_values") is not None:
      raise InvalidKeyError(
        "categorical_values", msg=f"Numerical parameter {parameter.name} cannot have `categorical_values`"
      )
    return

  categorical_values_json = get_with_validation(
    parameter_json,
    "categorical_values",
    ValidationType.arrayOf(ValidationType.oneOf([ValidationType.object, ValidationType.string])),
  )
  seen_names = set()
  for enum_index, categorical_value_json in enumerate(categorical_values_json or [], start=1):
    categorical_value = parameter.all_categorical_values.add()
    set_categorical_value_from_json(categorical_value, categorical_value_json, enum_index)

    if categorical_value.name in seen_names:
      raise InvalidValueError(f"Duplicate categorical value name: {categorical_value.name}")
    else:
      seen_names.add(categorical_value.name)

  if not parameter.all_categorical_values:
    raise BadParamError(f"No categorical values provided for categorical parameter {parameter.name}")
  elif len(parameter.all_categorical_values) == 1:
    raise BadParamError(f"Categorical parameter {parameter.name} should have at least 2 categorical values.")


def set_categorical_value_from_json(categorical_value, categorical_value_json, enum_index):
  categorical_value.enum_index = enum_index
  if is_string(categorical_value_json):
    categorical_value.name = categorical_value_json
  else:
    categorical_value.name = get_with_validation(categorical_value_json, "name", ValidationType.string)
    if get_opt_with_validation(categorical_value_json, "deleted", ValidationType.boolean):
      raise BadParamError(f"Categorical value {categorical_value.name} cannot be deleted at creation time.")
  categorical_value.name = validate_categorical_value(categorical_value.name)


def set_grid_values_from_json(parameter, parameter_json):
  grid = get_opt_with_validation(
    parameter_json,
    "grid",
    ValidationType.arrayOf(ValidationType.assignment),
  )

  if parameter.param_type == PARAMETER_CATEGORICAL and grid:
    raise GridError(
      parameter, "Categorical parameters cannot have a grid specified. `categorical_values` will be used as a grid."
    )

  if parameter.param_type != PARAMETER_CATEGORICAL and not grid:
    raise GridError(parameter, "Cannot be an empty list.")

  if parameter.param_type == PARAMETER_CATEGORICAL:
    # TODO(SN-1119): can this be handled a better way?
    parameter_proxy = ExperimentParameterProxy(parameter)
    grid = [c.enum_index for c in parameter_proxy.all_categorical_values]
  elif parameter.param_type == PARAMETER_DOUBLE:
    grid = get_with_validation(
      parameter_json,
      "grid",
      ValidationType.arrayOf(ValidationType.number),
    )
    grid = sorted(grid)
  elif parameter.param_type == PARAMETER_INT:
    grid = get_with_validation(
      parameter_json,
      "grid",
      ValidationType.arrayOf(ValidationType.integer),
    )
    grid = sorted(grid)
  else:
    raise GridError(
      parameter,
      "Grid experiment parameters must be double, int or categorical.",
    )

  grid_set = set(grid)
  if len(grid_set) != len(grid):
    raise GridError(parameter, "Cannot have duplicate values in grid.")

  if len(grid_set) < 2:
    raise GridError(parameter, "Must have 2 or more values in grid")

  if parameter.param_type != PARAMETER_CATEGORICAL:
    if parameter.transformation == ExperimentParameter.TRANSFORMATION_LOG:
      if any(val <= 0 for val in grid_set):
        raise GridError(parameter, "Values must be greater than zero when transformation log is specified")

  del parameter.grid_values[:]
  parameter.grid_values.extend(grid)


def set_default_value_from_json(parameter, parameter_json):
  default_value = get_opt_with_validation(parameter_json, "default_value", ValidationType.assignment)
  if default_value is not None:
    value_to_set = get_assignment(parameter, default_value)
    parameter.replacement_value_if_missing = value_to_set

    if parameter.transformation == ExperimentParameter.TRANSFORMATION_LOG:
      if parameter.replacement_value_if_missing <= 0.0:
        raise BadParamError("Invalid default_value for log-transformation: default_value must be positive")


def set_parameter_conditions_from_json(parameter, parameter_json, conditionals_map):
  conditions_json = get_opt_with_validation(
    parameter_json,
    "conditions",
    ValidationType.objectOf(
      ValidationType.oneOf([ValidationType.arrayOf(ValidationType.string), ValidationType.string])
    ),
  )

  if not conditions_json:
    return

  for (name_json, values_json) in conditions_json.items():
    condition = parameter.conditions.add()
    condition.name = name_json
    try:
      conditional = conditionals_map[condition.name]
    except KeyError as e:
      raise BadParamError(
        f"Parameter {parameter.name} attempted to use non-existent conditional {condition.name}"
      ) from e
    if not values_json:
      raise BadParamError(
        f"When providing condition for {condition.name} on parameter {parameter.name}, must provide at least one value"
      )
    values_json = values_json if is_sequence(values_json) else [values_json]
    values = []
    for value_json in values_json:
      conditional_value = find(conditional.values, lambda c: c.name == value_json)
      if conditional_value is None:
        raise BadParamError(
          f"Conditional {condition.name} on parameter {parameter.name} attempted to use non-existent value {value_json}"
        )
      values.append(conditional_value.enum_index)
    condition.values.extend(values)


def set_transformation_from_json(parameter, parameter_json):
  if parameter.param_type != PARAMETER_DOUBLE:
    if parameter_json.get("transformation") is not None:
      raise BadParamError("Transformation is only valid for parameters of type `double`")

  transformation_string = get_opt_with_validation(parameter_json, "transformation", ValidationType.string)
  if transformation_string:
    try:
      parameter.transformation = PARAMETER_TRANSFORMATION_NAME_TO_TYPE[transformation_string]
    except KeyError as e:
      raise InvalidValueError(
        f"Invalid parameter transformation: {transformation_string} must be one of "
        f"{list(PARAMETER_TRANSFORMATION_NAME_TO_TYPE.keys())}"
      ) from e
