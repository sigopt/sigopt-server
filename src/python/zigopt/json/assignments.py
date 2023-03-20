# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.experiment.model import Experiment  # type: ignore
from zigopt.json.render import conditionally_render_param_value, render_conditional_value


def assignments_json(experiment: Experiment, assignments_dict: dict[str, float]) -> dict[str, int | float | str | None]:

  parameters_map = experiment.all_parameters_including_deleted_map
  conditionals_map = experiment.conditionals_map

  json_dict: dict[str, int | float | str | None] = {
    **{
      name: render_conditional_value(conditionals_map[name], assignment)
      for (name, assignment) in assignments_dict.items()
      if name in conditionals_map
    },
    **{
      name: conditionally_render_param_value(parameters_map[name], assignment, assignments_dict)
      for (name, assignment) in assignments_dict.items()
      if name in parameters_map
    },
  }

  unknown_keys = set(assignments_dict.keys()) - set(json_dict.keys())
  if unknown_keys:
    raise Exception(f"Attempting to render assignments, unknown keys: {', '.join(unknown_keys)}")

  return json_dict
