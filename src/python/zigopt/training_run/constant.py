# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import TrainingRunData
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


TRAINING_RUN_STATE_JSON_ACTIVE = "active"
TRAINING_RUN_STATE_JSON_COMPLETED = "completed"
TRAINING_RUN_STATE_JSON_FAILED = "failed"

TRAINING_RUN_STATE_TO_JSON: dict[int, str]
TRAINING_RUN_JSON_TO_STATE: dict[str, int]
TRAINING_RUN_STATE_TO_JSON, TRAINING_RUN_JSON_TO_STATE = generate_constant_map_and_inverse(
  {
    TrainingRunData.ACTIVE: TRAINING_RUN_STATE_JSON_ACTIVE,
    TrainingRunData.COMPLETED: TRAINING_RUN_STATE_JSON_COMPLETED,
    TrainingRunData.FAILED: TRAINING_RUN_STATE_JSON_FAILED,
  }
)

NON_OPTIMIZED_SUGGESTION_TYPES = (
  UnprocessedSuggestion.Source.USER_CREATED,
  UnprocessedSuggestion.Source.GRID,
  UnprocessedSuggestion.Source.QUEUED_SUGGESTION,
  UnprocessedSuggestion.Source.EXPLICIT_RANDOM,
)
