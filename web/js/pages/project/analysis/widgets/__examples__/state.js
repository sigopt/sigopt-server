/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export const EXAMPLE_WIDGET_TYPE = "EXAMPLE_WIDGET";

import {widgetStateBuilder} from "../widget_state_builder";
/**
 * @typedef ExampleWidgetStateState
 * @type {object}
 * @property {string} exampleText
 * @property {string} selectedDimKey
 * @property {string} editorDimKey
 */

// ********WARNING********
// ALL OF THIS IS GOING TO GO INTO THE DB
// You want to save things like the dimension keys not the actual dimensions themselves.
// You NEED everything here. ie version, type, layout, state
/**
 * @typedef ExampleWidgetState
 * @type {object}
 * @property {number} version - Used for migrations, start at 1.
 * @property {string} type    - The type of the widget, make sure this unique amonst all widgets.
 * @property {object} layout  - Size for the widget see: https://github.com/STRML/react-grid-layout
 *                              Don't add x and y. Those will get added by the dashboard.
 * @property {string} title   - title/header for widget, falls back to displayName from ./index
 * @property {ExampleWidgetStateState} state - state for your widget,
 *                                             everything else is common for all widgets
 */

/**

 * @param {string} exampleText
 * @param {string} selectedDimKey
 * @returns {ExampleWidgetState}
 */
export const ExampleStateBuilder = (
  title,
  exampleText,
  selectedDimKey,
  editorDimKey,
) => {
  const height = Math.max(Math.ceil(exampleText.length / 100), 5);
  const layout = {w: 2, h: height, minH: 5, minW: 1, x: 4};
  const state = {exampleText, selectedDimKey, editorDimKey};

  return widgetStateBuilder(1, EXAMPLE_WIDGET_TYPE, layout, title, state);
};

// When making a new widget this will be fed into the editor.
export const ExamplenewWidgetStateBuilder = () => {
  const title = "";
  const exampleText = "";

  return ExampleStateBuilder(title, exampleText, null, null);
};
