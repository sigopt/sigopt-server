/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export const ParameterTypes = {
  CATEGORICAL: "categorical",
  DOUBLE: "double",
  INTEGER: "int",
};

export const ExperimentTypes = {
  GRID: "grid",
  OFFLINE: "offline",
  RANDOM: "random",
};

export const ExperimentStates = {
  ACTIVE: "active",
  DELETED: "deleted",
};

export const MetricStrategy = {
  OPTIMIZE: "optimize",
  STORE: "store",
  CONSTRAINT: "constraint",
};

export const InteractionStates = {
  CREATE: "create",
  MODIFY: "modify",
  READ_ONLY: "read_only",
};

export const ParameterTransformations = {
  LOG: "log",
  NONE: "none",
};
