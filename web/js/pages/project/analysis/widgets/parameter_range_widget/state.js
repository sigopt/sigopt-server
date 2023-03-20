/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export const PARAMETER_RANGE_WIDGET_TYPE = "PARAMETER_RANGE_WIDGET";

import {getParameterInfo} from "./widget";
import {widgetStateBuilder} from "../widget_state_builder";

export const ParameterRangeStateBuilder = (title, height) =>
  widgetStateBuilder(
    1,
    PARAMETER_RANGE_WIDGET_TYPE,
    {w: 2, h: height, minH: 4, minW: 1},
    title,
    {},
  );
export const ParameterRangeEditor = (fullReduxState) => {
  const numParameters = getParameterInfo(
    fullReduxState.dimensions.dimensions,
  ).length;
  const height = numParameters + 1;
  return ParameterRangeStateBuilder("Suggested Parameters", height);
};
