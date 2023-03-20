/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {EXAMPLE_WIDGET_TYPE, ExamplenewWidgetStateBuilder} from "./state";
import {ExampleWidget} from "./widget";
import {ExampleWidgetEditor} from "./editor";
export {EXAMPLE_WIDGET_TYPE} from "./state";

/**
 * @typedef {import('../widgets').WidgetIndex} WidgetIndex
 */

/** @type {WidgetIndex} */
export const ExampleWidgetDefinition = {
  newWidgetStateBuilder: ExamplenewWidgetStateBuilder,
  component: ExampleWidget,
  displayName: "Example Widget",
  editor: ExampleWidgetEditor,
  editorIsReactComponent: true,
  type: EXAMPLE_WIDGET_TYPE,
  removable: true,
};
