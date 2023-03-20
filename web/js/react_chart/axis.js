/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {
  CHART_COLORS,
  FONT_FAMILY,
  FONT_SIZE,
  TICK_FONT_SIZE,
} from "../chart/constants";

export default {
  gridcolor: CHART_COLORS.LINE,
  linecolor: CHART_COLORS.LINE,
  showline: true,
  tickfont: {
    color: CHART_COLORS.FONT,
    family: FONT_FAMILY,
    size: TICK_FONT_SIZE,
  },
  ticks: "outside",
  titlefont: {
    color: CHART_COLORS.FONT,
    family: FONT_FAMILY,
    size: FONT_SIZE,
  },
  zerolinecolor: CHART_COLORS.DARK_LINE,
  showexponent: "all",
  exponentformat: "e",
};
