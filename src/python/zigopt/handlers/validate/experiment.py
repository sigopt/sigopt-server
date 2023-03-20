# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy
from typing import Any, Optional

from zigopt.experiment.constant import (  # type: ignore
  ALL_METRIC_OBJECTIVE_NAMES,
  ALL_METRIC_STRATEGY_NAMES,
  EXPERIMENT_NAME_TO_TYPE,
  METRIC_OBJECTIVE_NAME_TO_TYPE,
  METRIC_STRATEGY_NAME_TO_TYPE,
)
from zigopt.experiment.model import Experiment  # type: ignore
from zigopt.handlers.validate.base import validate_name
from zigopt.handlers.validate.project import PROJECT_ID_SCHEMA as _PROJECT_ID_SCHEMA
from zigopt.handlers.validate.validate_dict import validate
from zigopt.net.errors import BadParamError  # type: ignore

from sigoptaux.constant import ConstraintType  # type: ignore


PROJECT_ID_SCHEMA = copy.deepcopy(_PROJECT_ID_SCHEMA)
PROJECT_ID_SCHEMA["type"] = ["string", "null"]

experiment_create_schema = {
  "definitions": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": Experiment.NAME_MAX_LENGTH,
    },
    "opt_name": {
      "type": ["string", "null"],
      "minLength": 1,
      "maxLength": Experiment.NAME_MAX_LENGTH,
    },
    "term": {
      "type": "object",
      "required": ["name", "weight"],
      "properties": {
        "name": {"$ref": "#/definitions/opt_name"},
        "weight": {"type": "number"},
      },
      "additionalProperties": False,
    },
    "task": {
      "type": "object",
      "required": ["name", "cost"],
      "properties": {
        "name": {"$ref": "#/definitions/opt_name"},
        "cost": {"type": "number"},
      },
      "additionalProperties": False,
    },
    "constraints": {
      "linear_ineq": {
        "type": "object",
        "required": ["type", "terms", "threshold"],
        "properties": {
          "type": {
            "type": "string",
            "enum": [ConstraintType.greater_than, ConstraintType.less_than],
          },
          "terms": {"type": "array", "items": {"$ref": "#/definitions/term"}},
          "threshold": {"type": "number"},
        },
        "additionalProperties": False,
      }
    },
  },
  "type": "object",
  "required": ["name"],
  "properties": {
    "name": {"$ref": "#/definitions/name"},
    "project": PROJECT_ID_SCHEMA,
    "type": {
      "type": ["string", "null"],
      "enum": list(EXPERIMENT_NAME_TO_TYPE.keys()) + [None],
    },
    "observation_budget": {
      "type": ["integer", "null"],
    },
    "budget": {
      "type": ["integer", "null"],
    },
    "metrics": {
      "type": ["array", "null"],
      "items": {
        "type": ["string", "object"],
        "properties": {
          "name": {"$ref": "#/definitions/opt_name"},
          "objective": {
            "type": ["string", "null"],
            "enum": ALL_METRIC_OBJECTIVE_NAMES + [None],
          },
          "strategy": {
            "type": ["string", "null"],
            "enum": ALL_METRIC_STRATEGY_NAMES + [None],
          },
          "threshold": {"type": ["number", "null"]},
          "object": {
            "type": ["string"],
            "enum": ["metric"],
          },
        },
        "additionalProperties": False,
      },
    },
    "parameters": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name": {"$ref": "#/definitions/name"},
          "conditions": {
            "type": "object",
            "additionalProperties": {
              "type": ["array", "string"],
              "items": {"type": "string"},
            },
          },
        },
      },
    },
    "conditionals": {
      "type": ["array", "null"],
      "items": {
        "type": "object",
        "required": ["name", "values"],
        "properties": {
          "name": {"$ref": "#/definitions/name"},
          "values": {
            "type": "array",
            "items": {"type": "string"},
          },
        },
        "additionalProperties": False,
      },
    },
    "linear_constraints": {
      "type": ["array", "null"],
      "items": {
        "type": "object",
        "required": ["type"],
        "oneOf": [{"$ref": "#/definitions/constraints/linear_ineq"}],
      },
    },
    "tasks": {
      "type": ["array", "null"],
      "items": {"type": "object", "required": ["name", "cost"], "oneOf": [{"$ref": "#/definitions/task"}]},
    },
    "metadata": {
      "type": ["object", "null"],
    },
    "num_solutions": {
      "type": ["integer", "null"],
    },
    "parallel_bandwidth": {
      "type": ["integer", "null"],
    },
    "runs_only": {
      "type": ["boolean", "null"],
    },
  },
}
experiment_update_schema = {
  "definitions": {
    "name": {
      "type": ["string", "null"],
      "minLength": 1,
      "maxLength": Experiment.NAME_MAX_LENGTH,
    },
  },
  "type": "object",
  "properties": {
    "project": PROJECT_ID_SCHEMA,
    "observation_budget": {
      "type": ["integer", "null"],
    },
    "budget": {
      "type": ["integer", "null"],
    },
    "state": {
      "type": ["string", "null"],
    },
    "name": {"$ref": "#/definitions/name"},
    "metrics": {
      "type": ["array", "null"],
      "items": {
        "type": ["string", "object"],
        "properties": {
          "name": {"$ref": "#/definitions/name"},
          "objective": {
            "type": ["string", "null"],
            "enum": ALL_METRIC_OBJECTIVE_NAMES + [None],
          },
          "strategy": {
            "type": ["string", "null"],
            "enum": ALL_METRIC_STRATEGY_NAMES + [None],
          },
          "threshold": {"type": ["number", "null"]},
          "object": {
            "type": ["string"],
            "enum": ["metric"],
          },
        },
        "additionalProperties": False,
      },
    },
    "parameters": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name": {"$ref": "#/definitions/name"},
        },
      },
    },
    "no_optimize": {},
    "metadata": {
      "type": ["object", "null"],
    },
    "parallel_bandwidth": {
      "type": ["integer", "null"],
    },
    "tasks": {
      "type": "array",
      "items": {"type": "object"},
    },
  },
}


def validate_experiment_json_dict_for_create(json_dict: dict[str, Any]) -> None:
  schema: dict[str, Any] = copy.deepcopy(experiment_create_schema)
  schema["additionalProperties"] = False
  validate(json_dict, schema)


def validate_experiment_json_dict_for_update(json_dict: dict[str, Any]) -> None:
  schema: dict[str, Any] = copy.deepcopy(experiment_update_schema)
  schema["additionalProperties"] = False
  validate(json_dict, schema)


def validate_name_length(obj_type: str, name: Optional[str]) -> str:
  if obj_type in ("Experiment", "Parameter", "Variable", "Metric", "Categorical"):
    name = validate_name(name)
    max_len = Experiment.CATEGORICAL_VALUE_MAX_LENGTH if obj_type == "Categorical" else Experiment.NAME_MAX_LENGTH
    if not name:
      raise BadParamError(f"{obj_type} names cannot be empty")
    if len(name) > max_len:
      raise BadParamError(f"{obj_type} names must be less than {max_len} characters")
    return name
  raise BadParamError(f"Unrecognized object type: {obj_type}")


def validate_experiment_name(name: Optional[str]) -> str:
  return validate_name_length("Experiment", name)


def validate_parameter_name(name: Optional[str]) -> str:
  return validate_name_length("Parameter", name)


def validate_variable_name(name: Optional[str]) -> str:
  return validate_name_length("Variable", name)


def validate_metric_name(name: Optional[str]) -> str:
  return validate_name_length("Metric", name)


def validate_metric_objective(objective: Optional[str]) -> Optional[int]:
  if objective in ALL_METRIC_OBJECTIVE_NAMES:
    return METRIC_OBJECTIVE_NAME_TO_TYPE[objective]
  elif objective is None:
    return None
  else:
    raise BadParamError(
      f"Unrecognized objective type: {objective} (If provided, must be one of {tuple(ALL_METRIC_OBJECTIVE_NAMES)})"
    )


def validate_metric_strategy(strategy: Optional[str]) -> Optional[int]:
  if strategy in ALL_METRIC_STRATEGY_NAMES:
    return METRIC_STRATEGY_NAME_TO_TYPE[strategy]
  elif strategy is None:
    return None
  else:
    raise BadParamError(
      f"Unrecognized strategy: {strategy}. If provided, must be one of {tuple(ALL_METRIC_STRATEGY_NAMES)}"
    )


def validate_categorical_value(name: Optional[str]) -> str:
  return validate_name_length("Categorical", name)


def validate_conditional_value(name: Optional[str]) -> str:
  return validate_categorical_value(name)


def validate_state(state: Optional[str]) -> Optional[str]:
  if state and state not in ("deleted", "active"):
    raise BadParamError(f'Unrecognized state {state} (if provided, must be one of ("deleted", "active")')
  return state
