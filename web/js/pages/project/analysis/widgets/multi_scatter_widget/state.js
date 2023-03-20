/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {DIMENSION_GROUP_TYPES} from "../../../data/dimensions";
import {
  GRADIENT_KEYS,
  GRADIENT_TYPES,
  createColorState,
} from "../../lib/color_dimension";
import {widgetStateBuilder} from "../widget_state_builder";

export const MULTI_SCATTER_WIDGET_TYPE = "MULTI_SCATTER_WIDGET";

/**
 * @typedef ColorDimensionState
 * @type {object}
 * @property {string} key - key of dimension to be used for the dimension
 * @property {Array<string>} xDimKeys - keys of x dimensions
 * @property {Array<string>} yDimKeys - keys of y dimensions
 * @property {string} colorDimKey - keys of dimension for color - optional
 */

/**
 * @typedef MultiScatterWidgetStateState
 * @type {object}

 * @property {Array<string>} xDimKeys - keys of x dimensions
 * @property {Array<string>} yDimKeys - keys of y dimensions
 * @property {object} colorState - colorDimension - optional
 */

// TODO: Figure out how to get jsdoc imports working properly

/**
 * @typedef MultiScatterWidgetState
 * @type {object}
 * @property {number} version - used for migrations
 * @property {string} type - the type of the widget
 * @property {object} layout - default layout for the widget
 * @property {string} title - title (used as header for widget)
 * @property {MultiScatterWidgetStateState} state - non-common state
 */

/**
 * @param {string} title
 * @param {Array<string>} xDimKeys
 * @param {Array<string>} yDimKeys
 * @returns {MultiScatterWidgetState}
 */
export const MultiScatterStateBuilder = (
  title,
  xDimKeys,
  yDimKeys,
  colorState,
) => {
  const height = yDimKeys.length * 4 + 2;
  const width = xDimKeys.length <= 1 ? 1 : 2;
  const layout = {w: width, h: height, minH: 3, minW: 1};
  const state = {xDimKeys, yDimKeys, colorState};

  return widgetStateBuilder(1, MULTI_SCATTER_WIDGET_TYPE, layout, title, state);
};

export const MultiScatterNewWidgetStateBuilder = () => {
  const title = "";
  const yDims = [];
  const xDims = [];

  return MultiScatterStateBuilder(title, xDims, yDims, {});
};

const DIMS_PER_AXIS = 3;
export const MultiScatterMetricParameterStateBuilder = (dims) => {
  const title = "Metrics X Parameters";
  const yDimsFull = _.compact(
    _.filter(dims, (d) => d.groupType === DIMENSION_GROUP_TYPES.METRIC).slice(
      0,
      DIMS_PER_AXIS,
    ),
  );
  const xDimsFull = _.compact(
    _.filter(
      dims,
      (d) => d.groupType === DIMENSION_GROUP_TYPES.PARAMETER,
    ).slice(0, DIMS_PER_AXIS),
  );
  const yDims = _.pluck(yDimsFull, "key");
  const xDims = _.pluck(xDimsFull, "key");

  const experimentDim = dims.experiment;
  let colorState = null;
  if (
    experimentDim &&
    experimentDim.categoricalValues &&
    experimentDim.categoricalValues.length > 1
  ) {
    colorState = createColorState(
      experimentDim.key,
      GRADIENT_TYPES.FIXED,
      GRADIENT_KEYS.FIXED.COLOR_BLIND_TEN,
    );
  }

  return MultiScatterStateBuilder(title, xDims, yDims, colorState);
};
