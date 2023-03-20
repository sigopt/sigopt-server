/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {DIMENSION_GROUP_TYPES} from "../../../data/dimensions";
import {PCChartStateBuilder} from "./state";

const MAX_METRIC_DIMS = 4;
const MAX_PARAMETER_DIMS = 3;
export const PCChartEditor = (fullReduxState) => {
  const dims = fullReduxState.dimensions.dimensions;

  const metricDims = _.compact(
    _.filter(dims, (d) => d.groupType === DIMENSION_GROUP_TYPES.METRIC).slice(
      0,
      MAX_METRIC_DIMS,
    ),
  );
  const metricDimKeys = _.pluck(metricDims, "key");
  const parameterDims = _.compact(
    _.filter(
      dims,
      (d) => d.groupType === DIMENSION_GROUP_TYPES.PARAMETER,
    ).slice(0, MAX_PARAMETER_DIMS),
  );
  const parameterDimKeys = _.pluck(parameterDims, "key");

  return PCChartStateBuilder(
    "Parallel Coordinates",
    [...metricDimKeys, ...parameterDimKeys],
    null,
  );
};
