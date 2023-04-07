# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.net.errors import BadParamError
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import FeatureImportances, SysMetadata


FEATURE_IMPORTANCES_MAX_NUM_FEATURE = 50
FEATURE_IMPORTANCES_KEY_MAX_LENGTH = 100


def validate_feature_importances(feature_importances: FeatureImportances) -> None:
  if len(feature_importances.scores) > FEATURE_IMPORTANCES_MAX_NUM_FEATURE:
    raise ValueError(
      f"Feature importances max feature number should be less than or equal to {FEATURE_IMPORTANCES_MAX_NUM_FEATURE}"
    )

  key_length = FEATURE_IMPORTANCES_KEY_MAX_LENGTH
  for key in feature_importances.scores:
    if len(key) > key_length:
      key_str = f"{key[:10]}...{key[-10:]}"
      raise BadParamError(
        f"The length of the feature_importances scores key '{key_str}' must be less than or equal to {key_length}"
      )
  key = feature_importances.type
  if len(key) > key_length:
    key_str = f"{key[:10]}...{key[-10:]}"
    raise BadParamError(
      f"The length of the feature_importances type '{key_str}' must be less than or equal to {key_length}"
    )


def validate_sys_metadata(metadata: SysMetadata) -> SysMetadata:
  assert isinstance(metadata, SysMetadata)
  validate_feature_importances(metadata.feature_importances)
  return metadata
