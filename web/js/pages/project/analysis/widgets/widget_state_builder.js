/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

// {w: 2, h: height, minH: 5, minW: 1};
/**
 * @typedef layout
 * @type {object}
 * width and height are effectively props to <ResponsiveGridLayout> (cols, rowHeight)
 * @property {number} w     -  width in react-grid-layout units
 * @property {number} h     -  height in react-grid-layout units
 * @property {number} minW  - minimumWidth of widget
 * @property {number} minH  - minimumHeight of widget
 */

/**
 *
 * @param {number} version
 * @param {string} type
 * @param {layout} layout
 * @param {string} title
 * @param {object} state
 */
export const widgetStateBuilder = (version, type, layout, title, state) => ({
  version,
  type,
  layout,
  title,
  state,
});
