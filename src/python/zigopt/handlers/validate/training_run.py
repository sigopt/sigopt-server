# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any, Mapping, Optional

from zigopt.net.errors import BadParamError  # type: ignore
from zigopt.training_run.constant import TRAINING_RUN_JSON_TO_STATE  # type: ignore
from zigopt.training_run.model import OPTIMIZED_ASSIGNMENT_SOURCE, TrainingRun  # type: ignore


MAX_SOURCE_LENGTH = 30


def validate_state(state_string: Optional[str]) -> str:
  if state_string is None:
    raise BadParamError("Invalid state: cannot be null")
  try:
    state = TRAINING_RUN_JSON_TO_STATE[state_string]
  except KeyError as e:
    raise BadParamError(f"Invalid state: {state_string}") from e
  return state


def validate_assignments_meta_json(assignments_meta: dict[str, dict[str, Any]]) -> None:
  for param, meta in assignments_meta.items():
    if len(meta["source"]) > MAX_SOURCE_LENGTH:
      raise BadParamError(
        f"The source {meta['source']} is over the maximum length of {MAX_SOURCE_LENGTH}"
        f" characters for the parameter {param}"
      )


def validate_assignments_sources_json(assignment_sources: dict[str, Any]) -> None:
  for key in assignment_sources.keys():
    if len(key) > MAX_SOURCE_LENGTH:
      raise BadParamError(f" {key} is over the maximum length of {key} characters for a parameter source.")


def validate_assignments_meta(
  input_params: Mapping[str, Any],
  input_params_meta: Mapping[str, Any],
  training_run: TrainingRun,
):
  sources = {meta.source for meta in dict(input_params_meta).values()}
  meta_keys = list(dict(input_params_meta).keys())
  params = list(dict(input_params).keys())
  if training_run:
    params += [*dict(training_run.training_run_data.assignments_struct)]

  if OPTIMIZED_ASSIGNMENT_SOURCE in sources:
    raise BadParamError(f" {OPTIMIZED_ASSIGNMENT_SOURCE} source is reserved and set automatically.")

  metas_without_param = set(meta_keys) - set(params)
  if metas_without_param:
    raise BadParamError(f" Parameter meta exist for {metas_without_param} but there is no corresponding parameter.")
