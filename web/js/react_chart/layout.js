/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import defaultAxis from "./axis";
import {CHART_COLORS, FONT_FAMILY, FONT_SIZE} from "../chart/constants";

export default {
  xaxis: _.extend(
    {
      showgrid: false,
    },
    defaultAxis,
  ),
  yaxis: _.extend(
    {
      showgrid: true,
    },
    defaultAxis,
  ),
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: CHART_COLORS.MEDIUM_GREY,
  margin: {
    t: 25,
    r: 25,
  },
  font: {
    color: CHART_COLORS.FONT,
    family: FONT_FAMILY,
    size: FONT_SIZE,
  },
};
