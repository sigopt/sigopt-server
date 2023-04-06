# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections import defaultdict
from copy import deepcopy

from zigopt.common import *
from zigopt.handlers.validate.validate_dict import ValidationType, get_with_validation
from zigopt.handlers.validate.web_data.ag_run_view import ag_run_view_schema
from zigopt.handlers.validate.web_data.run_view import run_view_schema
from zigopt.net.errors import BadParamError
from zigopt.web_data.lib import validate_web_data_dict
from zigopt.web_data.model import MAX_DISPLAY_NAME_LENGTH, web_data_types_by_resource

from libsigopt.aux.validate_schema import validate


parent_resource_types = list(web_data_types_by_resource.keys())
web_data_types = flatten([web_data_types_by_resource[key].keys() for key in parent_resource_types])

base_web_data_schema = {
  "type": "object",
  "required": ["payload", "parent_resource_type", "web_data_type", "parent_resource_id"],
  "additionalProperties": False,
  "properties": {
    "parent_resource_id": {"type": ["object", "string"]},
    "payload": {"type": "object"},
    "parent_resource_type": {"type": "string", "enum": parent_resource_types},
    "web_data_type": {"type": "string", "enum": web_data_types},
    "display_name": {"type": "string", "maxLength": MAX_DISPLAY_NAME_LENGTH},
  },
}

schema_by_resource = {"project": {"run_view": run_view_schema, "ag_run_view": ag_run_view_schema}}
validate_web_data_dict(schema_by_resource)

# Special case for project since it doesn't have single unique ID, everything else can use a regular id
project_parent_id_schema = {
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "client": {"type": "string"},
    "project": {"type": "string"},
  },
}
rest_parent_id_schema = {"type": "string"}


def project_parent_id_validator(parent_resource_id):
  validate(parent_resource_id, project_parent_id_schema)
  get_with_validation(parent_resource_id, "client", ValidationType.id)
  get_with_validation(parent_resource_id, "project", ValidationType.id_string)


def rest_parent_id_validator(parent_resource_id):
  validate(parent_resource_id, rest_parent_id_schema)
  get_with_validation({"id": parent_resource_id}, "id", ValidationType.id)


parent_id_validator_by_resource = defaultdict(
  lambda: rest_parent_id_validator,
  {
    "project": project_parent_id_validator,
  },
)
validate_web_data_dict(parent_id_validator_by_resource, depth=1)


def validate_resource_exists(parent_resource_type, web_data_type):
  test = schema_by_resource.get(parent_resource_type, {}).get(web_data_type, None)
  if test is None:
    raise BadParamError(f"Could not find web data type: `{web_data_type}` for resource: `{parent_resource_type}`")


def validate_web_data_parent_resource_id(params):
  parent_id_validator = parent_id_validator_by_resource[params["parent_resource_type"]]
  parent_id_validator(params["parent_resource_id"])
  validate_resource_exists(params["parent_resource_type"], params["web_data_type"])


def validate_web_data_create(params):
  validate(params, base_web_data_schema)
  validate_web_data_parent_resource_id(params)

  payload_validator = schema_by_resource.get(params["parent_resource_type"]).get(params["web_data_type"])
  validate(params["payload"], payload_validator)


list_web_data_schema = deepcopy(base_web_data_schema)
del list_web_data_schema["properties"]["payload"]
list_web_data_schema["required"].remove("payload")


def validate_web_data_list(params):
  validate(params, list_web_data_schema)
  validate_web_data_parent_resource_id(params)


update_web_data_schema = deepcopy(base_web_data_schema)
update_web_data_schema["required"].append("id")
update_web_data_schema["properties"]["id"] = {"type": "string"}


def validate_web_data_update(params):
  validate(params, update_web_data_schema)
  validate_web_data_parent_resource_id(params)

  get_with_validation(params, "id", ValidationType.id)

  payload_validator = schema_by_resource.get(params["parent_resource_type"]).get(params["web_data_type"])
  validate(params["payload"], payload_validator)


delete_web_data_schema = deepcopy(base_web_data_schema)
delete_web_data_schema["required"].append("id")
delete_web_data_schema["properties"]["id"] = {"type": "string"}
del delete_web_data_schema["properties"]["payload"]
delete_web_data_schema["required"].remove("payload")


def validate_web_data_delete(params):
  validate(params, delete_web_data_schema)
  validate_web_data_parent_resource_id(params)

  get_with_validation(params, "id", ValidationType.id)
