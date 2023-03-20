/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {isDefinedAndNotNull} from "../utils";

const CHART_RANGE_DEFAULT_PADDING = 5 / 100;
const CHART_RANGE_DEFAULT_RADIUS = 1;

export const getChartRange = (
  min,
  max,
  {
    padding = CHART_RANGE_DEFAULT_PADDING,
    radius = CHART_RANGE_DEFAULT_RADIUS,
  } = {},
) => {
  const computeRange = (l, r) => [l - (r - l) * padding, r + (r - l) * padding];
  const defined = _.map([min, max], isDefinedAndNotNull);
  if (_.all(defined) && min < max) {
    return computeRange(min, max);
  }
  if (_.any(defined)) {
    const focus = _.find([min, max], isDefinedAndNotNull);
    return computeRange(focus - radius, focus + radius);
  }
  return computeRange(0, 1);
};
