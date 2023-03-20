/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export const RUN_TABLE_WIDGET_TYPE = "RUN_TABLE_WIDGET";

export const RunTableStateBuilder = (title, tableState) => ({
  version: 1,
  type: RUN_TABLE_WIDGET_TYPE,
  layout: {w: 2, h: 8, minH: 3, minW: 1},
  title,
  state: {tableState},
});

export const RunTableEditor = () => RunTableStateBuilder("Runs", null);
