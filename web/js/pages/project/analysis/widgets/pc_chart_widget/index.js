/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {ConnectedPCChartWidget} from "./widget";
import {PCChartEditor} from "./editor";
import {PC_CHART_WIDGET_TYPE} from "./state";

/**
 * @typedef {import('../widgets').WidgetIndex} WidgetIndex
 */

/** @type {WidgetIndex} */
export const PCChartWidgetDefinition = {
  newWidgetStateBuilder: null,
  component: ConnectedPCChartWidget,
  type: PC_CHART_WIDGET_TYPE,
  displayName: "Parallel Coordinates Chart",
  editor: PCChartEditor,
  editorIsReactComponent: false,
  removable: true,
};
