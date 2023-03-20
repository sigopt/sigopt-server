/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Chart from "./chart";
import {AxisTypes, CHART_COLORS} from "./constants";
import {isDefinedAndNotNull} from "../utils";
import {updateLayoutForThresholds} from "./thresholds";

class ImprovementChart extends Chart {
  styledTrace(trace) {
    return {
      hoverinfo: "y",
      mode: "lines+markers",
      name: trace.name,
      type: "scatter",
      observation_ids: _.chain(trace.points).pluck("point").pluck("id").value(),
      x: _.range(1, trace.points.length + 1),
      y: _.pluck(trace.points, "value"),
    };
  }

  getChartArgs(experiment, traces) {
    if (!traces) {
      return null;
    }
    const lengths = _.map(traces, (t) => t.points.length);
    const maxRange = _.max(
      lengths.concat(
        experiment.tasks ? [1] : [experiment.observation_budget, 1],
      ),
    );

    const colors = [CHART_COLORS.BLUE, CHART_COLORS.GREY];
    const sizes = experiment.tasks ? [9, 6] : [7];
    const chartLayout = {
      showlegend: isDefinedAndNotNull(experiment.tasks),
      margin: {
        l: 80,
        r: 65,
      },
      xaxis: {
        autorange: false,
        autotick: true,
        range: [0, maxRange + 1],
        rangemode: "tozero",
        tickformat: "d",
        title: "Trials",
      },
      yaxis: {
        title: "Best Value",
        showexponent: "all",
        exponentformat: "e",
      },
    };
    updateLayoutForThresholds(
      experiment,
      _.chain(traces)
        .pluck("points")
        .flatten(true)
        .filter()
        .pluck("point")
        .value(),
      {yAxis: {type: AxisTypes.OPTIMIZED_METRIC}},
      chartLayout,
    );
    return {
      data: _.map(traces, (t, index) =>
        _.extend(this.styledTrace(t), {
          line: {
            width: 0.5,
            color: CHART_COLORS.LINE,
          },
          marker: {
            size: sizes[index],
            color: colors[index],
          },
        }),
      ),
      layout: chartLayout,
    };
  }
}

export default ImprovementChart;
