/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {ConnectedRunInfoWidget} from "./widget";
import {RUN_INFO_WIDGET_TYPE, RunInfoEditor} from "./state";

/**
 * @typedef {import('../widgets').WidgetIndex} WidgetIndex
 */

/** @type {WidgetIndex} */
export const RunInfoWidgetDefinition = {
  newWidgetStateBuilder: null,
  component: ConnectedRunInfoWidget,
  displayName: "Run Details",
  editor: RunInfoEditor,
  editorIsReactComponent: false,
  type: RUN_INFO_WIDGET_TYPE,
  removable: true,
};
