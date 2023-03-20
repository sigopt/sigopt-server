# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any, Optional

from zigopt.experiment.model import Experiment  # type: ignore
from zigopt.handlers.validate.validate_dict import key_present
from zigopt.net.errors import BadParamError  # type: ignore


def validate_state(state: Optional[str]) -> Optional[str]:
  if state and state != "open":
    raise BadParamError(f"Unrecognized state {state} (if provided, must be open)")
  return state


def validate_suggestion_json_dict_for_create(json_dict: dict[str, Any], experiment: Experiment) -> None:
  if experiment.is_multitask:
    if (key_present(json_dict, "assignments") and not key_present(json_dict, "task")) or (
      key_present(json_dict, "task") and not key_present(json_dict, "assignments")
    ):
      raise BadParamError(
        "For multitask experiments, manually created suggestions must have both `assignments` and `task`"
      )
  else:
    if key_present(json_dict, "task"):
      raise BadParamError("`task` should only be present for multitask experiments")
