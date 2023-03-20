/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export const RUN_INFO_WIDGET_TYPE = "RUN_INFO_WIDIGET";

import {widgetStateBuilder} from "../widget_state_builder";

export const RunInfoStateBuilder = (title) =>
  widgetStateBuilder(
    1,
    RUN_INFO_WIDGET_TYPE,
    {w: 1, h: 6, minH: 4, minW: 1},
    title,
    {},
  );
export const RunInfoEditor = () => {
  return RunInfoStateBuilder("Run Details");
};
