/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {ConnectedParameterRangeWidget} from "./widget";
import {PARAMETER_RANGE_WIDGET_TYPE, ParameterRangeEditor} from "./state";

/**
 * @typedef {import('../widgets').WidgetIndex} WidgetIndex
 */

/** @type {WidgetIndex} */
export const ParamaterRangeWidgetDefinition = {
  newWidgetStateBuilder: null,
  component: ConnectedParameterRangeWidget,
  displayName: "Suggested Parameters",
  editor: ParameterRangeEditor,
  editorIsReactComponent: false,
  type: PARAMETER_RANGE_WIDGET_TYPE,
  removable: true,
};
