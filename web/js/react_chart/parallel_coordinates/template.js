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
} from "../../chart/constants";

export const parallelCoordinatesTemplates = {
  base_template: {
    options: {
      // list - https://github.com/plotly/plotly.js/blob/35fb5b918e3dbdc3cc6e3b9735c8003008376020/src/components/modebar/buttons.js - as of 2022-10-26
      modeBarButtonsToRemove: [
        "autoScale2d",
        "displayLogo",
        "hoverClosestCartesian",
        "hoverClosestGl2d",
        "hoverCompareCartesian",
        "pan2d",
        "resetScale2d",
        "sendDataToCloud",
        "toggleSpikelines",
        "zoom2d",
        "zoomIn2d",
        "zoomOut2d",
        "toImage",
      ],
      displaylogo: false,
      displayModeBar: false,
      showlegend: "false",
    },
    layout: {
      paper_bgcolor: "rgba(0,0,0,0)",
      margin: {
        t: 40,
        b: 40,
      },
    },
    data: [
      {
        type: "parcoords",
        line: {
          color: "#0098D1",
        },
        labelfont: {
          color: CHART_COLORS.FONT,
          family: FONT_FAMILY,
          size: FONT_SIZE,
        },
        tickfont: {
          color: CHART_COLORS.LIGHT_BLACK,
          family: FONT_FAMILY,
          size: TICK_FONT_SIZE,
        },
        dimensions: [],
      },
    ],
  },

  fragments: {
    scaleline: {
      showscale: true,
      colorscale: CHART_COLORS.METRIC_GRADIENT,
      colorbar: {
        titlefont: {
          color: CHART_COLORS.FONT,
          family: FONT_FAMILY,
          size: FONT_SIZE,
        },
        tickfont: {
          color: CHART_COLORS.FONT,
          family: FONT_FAMILY,
          size: TICK_FONT_SIZE,
        },
      },
    },

    basicline: {
      color: CHART_COLORS.BLUE,
    },

    paretoline: {
      colorscale: [
        [0, CHART_COLORS.BLUE],
        [1, CHART_COLORS.ORANGE],
      ],
      cmin: 0,
      cmax: 1,
    },
  },
};
