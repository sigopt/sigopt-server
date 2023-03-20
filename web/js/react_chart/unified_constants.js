/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";

import {AxisTypes} from "../chart/constants";

export const AxisOrder = {
  DEFAULT: [
    AxisTypes.PARAMETER,
    AxisTypes.OPTIMIZED_METRIC,
    AxisTypes.CONSTRAINED_METRIC,
    AxisTypes.STORED_METRIC,
    AxisTypes.CONDITIONAL,
    AxisTypes.METADATA,
  ],
  METRICS_FIRST: [
    AxisTypes.OPTIMIZED_METRIC,
    AxisTypes.CONSTRAINED_METRIC,
    AxisTypes.STORED_METRIC,
    AxisTypes.PARAMETER,
    AxisTypes.CONDITIONAL,
    AxisTypes.METADATA,
  ],
};

export const ChartTypes = {
  Scatter2D: {axesCount: 2, key: "0", label: "2D"},
  Scatter3D: {axesCount: 3, key: "1", label: "3D"},
  // NOTE: axesCount is 3 here because this chart is viable even if
  // the highlight axis is equivalent to another axis
  Scatter3DWithHighlight: {axesCount: 3, key: "2", label: "3D with highlight"},
};

export const chartTypesProp = PropTypes.shape({
  axesCount: PropTypes.number.isRequired,
  key: PropTypes.string.isRequired,
  label: PropTypes.oneOf(_.pluck(ChartTypes, "label")).isRequired,
});

export const axisDefaultsProp = PropTypes.shape({
  label: PropTypes.string.isRequired,
  type: AxisTypes.isRequired,
});

export const PlotlyAxisScales = {
  DEFAULT: "-",
  LOG: "log",
};
