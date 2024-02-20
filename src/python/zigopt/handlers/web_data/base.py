# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json

from zigopt.common import *
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.validate.web_data.base import validate_web_data_parent_resource_id
from zigopt.web_data.lib import validate_web_data_dict

from libsigopt.aux.errors import SigoptValidationError


web_data_limits = {"project": {"run_view": 100, "ag_run_view": 100}}
validate_web_data_dict(web_data_limits)


class WebDataBaseHandler(Handler):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.web_data_limits = web_data_limits

  def can_act_on_objects(self, requested_permission, objects):
    params = self._request.request.params()

    if (parent_resource_id := params.get("parent_resource_id", None)) is None:
      raise SigoptValidationError("No parent_resource_id set.")

    # For list/delete parent_resource_id is stringified to fit inside query params
    if is_string(parent_resource_id):
      try:
        params["parent_resource_id"] = json.loads(parent_resource_id)
      except Exception as e:
        raise SigoptValidationError("parent_resource_id should be a string id or JSON object for projects") from e

    validate_web_data_parent_resource_id(params)
    can_act_on_resource = {
      "project": self.can_act_on_project,
    }
    validate_web_data_dict(can_act_on_resource, depth=1)

    can_act = can_act_on_resource[params["parent_resource_type"]](params["parent_resource_id"], requested_permission)
    return can_act is True and super().can_act_on_objects(requested_permission, objects)

  def can_act_on_project(self, parent_resource_id, requested_permission):
    assert self.auth is not None

    project = self.services.project_service.find_by_client_and_reference_id(
      parent_resource_id["client"], parent_resource_id["project"]
    )

    return self.auth.can_act_on_project(self.services, requested_permission, project)
