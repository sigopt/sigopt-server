/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {
  MULTI_SCATTER_WIDGET_TYPE,
  MultiScatterNewWidgetStateBuilder,
} from "./state";
import {MultiScatterWidget} from "./widget";
import {MultiScatterWidgetEditor} from "./editor";
export {MULTI_SCATTER_WIDGET_TYPE} from "./state";

/**
 * @typedef {import('../widgets').WidgetIndex} WidgetIndex
 */

/** @type {WidgetIndex} */
export const MultiScatterWidgetDefinition = {
  newWidgetStateBuilder: MultiScatterNewWidgetStateBuilder,
  component: MultiScatterWidget,
  type: MULTI_SCATTER_WIDGET_TYPE,
  displayName: "Linked Scatter Plots",
  editor: MultiScatterWidgetEditor,
  editorIsReactComponent: true,
  removable: true,
};
