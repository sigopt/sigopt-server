/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {DIMENSION_GROUP_TYPES} from "../../../data/dimensions";

export const PC_CHART_WIDGET_TYPE = "PC_CHART_SCATTER_WIDGET";

export const PCChartStateBuilder = (title, selectedDims, colorState) => ({
  version: 1,
  type: PC_CHART_WIDGET_TYPE,
  layout: {w: 2, h: 5, minH: 3, minW: 1},
  title,
  state: {selectedDims, colorState},
});

const MAX_METRIC_DIMS = 4;
const MAX_PARAMETER_DIMS = 4;
export const PCChartProjectStateBuilder = (dims) => {
  const metricDims = _.compact(
    _.filter(dims, (d) => d.groupType === DIMENSION_GROUP_TYPES.METRIC).slice(
      0,
      MAX_METRIC_DIMS,
    ),
  );
  const parameterDims = _.compact(
    _.filter(
      dims,
      (d) => d.groupType === DIMENSION_GROUP_TYPES.PARAMETER,
    ).slice(0, MAX_PARAMETER_DIMS),
  );

  const metricDimKeys = _.pluck(metricDims, "key");
  const parameterDimsKeys = _.pluck(parameterDims, "key");

  return PCChartStateBuilder(
    "Parallel Coordinates",
    [...metricDimKeys, ...parameterDimsKeys],
    null,
  );
};
