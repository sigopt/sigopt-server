/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import ui from "../experiment/ui";
import {AxisTypes} from "../chart/constants";
import {axisValueGetter} from "../chart/values";
import {getChartRange} from "../chart/range";
import {isDefinedAndNotNull, isUndefinedOrNull} from "../utils";

const thresholdLineStyle = {
  color: "red",
  width: 1,
};
const thresholdBoxFillColor = "rgba(50, 50, 50, 0.3)";

const getThresholdShapes = (experiment, axesOptions) => {
  const orientThreshold = ({axis, max, min}) => {
    const [l, r] = getChartRange(min, max, {padding: 2});
    return ui.metricObjectiveOption(ui.findMetric(experiment, axis.key), {
      minimize: [l, r],
      maximize: [r, l],
    });
  };
  const [xOptions, yOptions] = axesOptions;
  if (xOptions && yOptions) {
    const [tx, ox] = orientThreshold(xOptions);
    const [ty, oy] = orientThreshold(yOptions);
    const outerBorder = {x: ox, y: oy};
    const thresholdBorder = {x: tx, y: ty};
    const center = {
      x: xOptions.threshold,
      y: yOptions.threshold,
    };
    return [
      // x threshold line
      //
      //    x
      //    |
      //    *--
      //
      {
        xref: "x",
        yref: "y",
        x0: center.x,
        y0: center.y,
        x1: center.x,
        y1: thresholdBorder.y,
        type: "line",
        line: thresholdLineStyle,
      },

      // y threshold line
      //
      //    |
      //    *--y
      //
      {
        xref: "x",
        yref: "y",
        x0: center.x,
        y0: center.y,
        x1: thresholdBorder.x,
        y1: center.y,
        type: "line",
        line: thresholdLineStyle,
      },

      // lower right box
      //
      //    |
      //    *--
      //     BOX
      //
      {
        xref: "x",
        yref: "y",
        x0: center.x,
        y0: center.y,
        x1: thresholdBorder.x,
        y1: outerBorder.y,
        type: "rect",
        line: {width: 0},
        fillcolor: thresholdBoxFillColor,
      },

      // lower left box
      //
      //    |
      //    *--
      // BOX
      //
      {
        xref: "x",
        yref: "y",
        x0: center.x,
        y0: center.y,
        x1: outerBorder.x,
        y1: outerBorder.y,
        type: "rect",
        line: {width: 0},
        fillcolor: thresholdBoxFillColor,
      },

      // upper left box
      //
      // BOX|
      //    *--
      //
      {
        xref: "x",
        yref: "y",
        x0: center.x,
        y0: center.y,
        x1: outerBorder.x,
        y1: thresholdBorder.y,
        type: "rect",
        line: {width: 0},
        fillcolor: thresholdBoxFillColor,
      },
    ];
  } else if (xOptions || yOptions) {
    const options = xOptions || yOptions;
    const threshold = options.threshold;
    const forX = options === xOptions;
    const outerBorder = orientThreshold(options)[1];
    return forX
      ? [
          // line
          {
            xref: "x",
            yref: "paper",
            x0: threshold,
            y0: 0,
            x1: threshold,
            y1: 1,
            type: "line",
            line: thresholdLineStyle,
          },

          // box
          {
            xref: "x",
            yref: "paper",
            x0: threshold,
            y0: 0,
            x1: outerBorder,
            y1: 1,
            type: "rect",
            line: {width: 0},
            fillcolor: thresholdBoxFillColor,
          },
        ]
      : [
          // line
          {
            xref: "paper",
            yref: "y",
            x0: 0,
            y0: threshold,
            x1: 1,
            y1: threshold,
            type: "line",
            line: thresholdLineStyle,
          },

          // box
          {
            xref: "paper",
            yref: "y",
            x0: 0,
            y0: threshold,
            x1: 1,
            y1: outerBorder,
            type: "rect",
            line: {width: 0},
            fillcolor: thresholdBoxFillColor,
          },
        ];
  }
  return [];
};

export const updateLayoutForThresholds = (
  experiment,
  observations,
  {xAxis, yAxis},
  layout,
) => {
  const axes = [xAxis, yAxis];
  const makeOptions = (axis, threshold) => {
    if (isUndefinedOrNull(threshold)) {
      return null;
    }
    const valuesWithThreshold = _.chain([
      _.map(observations, axisValueGetter(axis)),
      threshold,
    ])
      .flatten(true)
      .filter(isDefinedAndNotNull)
      .value();
    const options = {
      axis,
      min: _.min(valuesWithThreshold),
      max: _.max(valuesWithThreshold),
      threshold,
    };
    options.axisLayout = {
      autorange: false,
      range: getChartRange(options.min, options.max),
    };
    return options;
  };
  const [xThreshold, yThreshold] = _.map(axes, (axis) =>
    axis &&
    _.contains(
      [AxisTypes.OPTIMIZED_METRIC, AxisTypes.CONSTRAINED_METRIC],
      axis.type,
    )
      ? ui.getThreshold(experiment, axis.key)
      : null,
  );
  const axesOptions = [
    makeOptions(xAxis, xThreshold),
    makeOptions(yAxis, yThreshold),
  ];
  layout.shapes = (layout.shapes || []).concat(
    getThresholdShapes(experiment, axesOptions),
  );
  const [xOptions, yOptions] = axesOptions;
  const extendLayout = ([options, key]) => {
    if (options) {
      layout[key] = _.extend({}, layout[key], options.axisLayout);
    }
  };
  _.each(
    [
      [xOptions, "xaxis"],
      [yOptions, "yaxis"],
    ],
    extendLayout,
  );
};
