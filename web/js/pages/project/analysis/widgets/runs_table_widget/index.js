/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {ConnectedRunTableWidget} from "./widget";
import {RUN_TABLE_WIDGET_TYPE, RunTableEditor} from "./state";

/**
 * @typedef {import('../widgets').WidgetIndex} WidgetIndex
 */

/** @type {WidgetIndex} */
export const RunTableWidgetDefinition = {
  newWidgetStateBuilder: null,
  component: ConnectedRunTableWidget,
  type: RUN_TABLE_WIDGET_TYPE,
  displayName: "Runs Table",
  editor: RunTableEditor,
  editorIsReactComponent: false,
  removable: false,
};
