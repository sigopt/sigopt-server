/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {CHECKPOINTS_WIDGET_TYPE, CheckpointEditorStateBuilder} from "./state";
import {CheckpointsWidgetEditor} from "./editor";
import {ConnectedCheckpointsChartWidget} from "./widget";
export {CHECKPOINTS_WIDGET_TYPE} from "./state";

/**
 * @typedef {import('../widgets').WidgetIndex} WidgetIndex
 */

/** @type {WidgetIndex} */
export const CheckpointsWidgetDefinition = {
  newWidgetStateBuilder: CheckpointEditorStateBuilder,
  component: ConnectedCheckpointsChartWidget,
  displayName: "Checkpoints Chart",
  editorIsReactComponent: true,
  editor: CheckpointsWidgetEditor,
  type: CHECKPOINTS_WIDGET_TYPE,
  removable: true,
};
