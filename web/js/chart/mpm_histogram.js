/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Chart from "./chart";
import layout from "../react_chart/layout";
import {CHART_COLORS} from "./constants";
import {isDefinedAndNotNull} from "../utils";

const getFilteredValues = (rs, metricName) =>
  _.chain(rs)
    .pluck("values")
    .pluck(metricName)
    .pluck("value")
    .filter(isDefinedAndNotNull)
    .value();

export default class MpmHistogram extends Chart {
  getChartData(metricName, runs, focusedRuns) {
    const focusedRunsIdSet = _.indexBy(focusedRuns, "id");
    const mainTrace = {
      x: getFilteredValues(
        _.reject(runs, (run) => focusedRunsIdSet[run.id]),
        metricName,
      ),
    };
    mainTrace.color = CHART_COLORS.DARK_BLUE;
    const traceData = [mainTrace];
    const secondaryTrace = {
      x: getFilteredValues(focusedRuns, metricName),
    };
    secondaryTrace.color = CHART_COLORS.BLUE;
    traceData.push(secondaryTrace);
    return traceData.reverse();
  }

  getChartArgs({metricName, runs, focusedRuns}) {
    const chartData = _.map(
      this.getChartData(metricName, runs, focusedRuns),
      (trace, traceIndex) => {
        let traceName;
        const traceLabels = this.args.traceLabels || {};
        if (_.size(chartData) > 1) {
          traceName =
            traceIndex === 0
              ? traceLabels.highlight || "Highlighted"
              : traceLabels.other || "Other";
        } else {
          traceName = traceLabels.total || "Total";
        }
        return {
          x: trace.x,
          marker: {color: trace.color},
          name: traceName,
          nbinsx: 64,
          type: "histogram",
          xaxis: "x",
        };
      },
    );
    // Note: This additional, hidden trace has the combined range
    // of all runs' values so that the "This Run" tickmark
    // aligns with the appropriate bin.
    if (this.args.showThisRun) {
      const allRuns = runs;
      if (_.first(focusedRuns).deleted === true) {
        allRuns.push(_.first(focusedRuns));
      }
      chartData.push({
        x: getFilteredValues(allRuns, metricName),
        hoverinfo: "skip",
        opacity: 0,
        nbinsx: 64,
        type: "histogram",
        xaxis: "x2",
      });
    }

    return {
      data: chartData,
      layout: _.extend(_.omit(layout, "margin"), {
        barmode: "stack",
        hovermode: true,
        plot_bgcolor: CHART_COLORS.LIGHT_GREY_BG,
        xaxis: _.extend(layout.xaxis, {
          fixedrange: true,
          linecolor: CHART_COLORS.MEDIUM_GREY_LINES,
          tickcolor: CHART_COLORS.MEDIUM_GREY_LINES,
          zeroline: false,
        }),
        ...(this.args.showThisRun
          ? {
              xaxis2: {
                color: CHART_COLORS.BLUE,
                fixedrange: true,
                overlaying: "x",
                tickcolor: CHART_COLORS.LIGHT_BLUE,
                ticktext: ["This Run"],
                ticklen: 23,
                tickvals: [_.first(getFilteredValues(focusedRuns, metricName))],
                tickwidth: 1,
              },
            }
          : {}),
        yaxis: _.extend(layout.yaxis, {
          automargin: true,
          gridcolor: CHART_COLORS.MEDIUM_GREY_LINES,
          showline: false,
          tickcolor: CHART_COLORS.MEDIUM_GREY_LINES,
          tickformat: ",d",
          zeroline: false,
        }),
      }),
    };
  }
}
