/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import ScatterPlot from "./scatter_plot";
import ui from "../experiment/ui";
import {
  AxisTypes,
  CHART_COLORS,
  FONT_FAMILY,
  FONT_SIZE,
  TICK_FONT_SIZE,
} from "./constants";
import {isDefinedAndNotNull} from "../utils";

class ScatterPlot4D extends ScatterPlot {
  defaultZAxisLayout() {
    return this.defaultAxisLayout();
  }

  getDataFromObservation(axes, plot, o, obsToRunMap) {
    const zValue = axes.z.getDataFromObservation(o);
    const wValue = axes.w && axes.w.getDataFromObservation(o);
    if (
      isDefinedAndNotNull(zValue) &&
      (!axes.w || !plot.highlight || isDefinedAndNotNull(wValue))
    ) {
      const data2d = super.getDataFromObservation(axes, plot, o, obsToRunMap);
      if (data2d) {
        return _.extend(data2d, {
          z: zValue,
          w: wValue,
        });
      }
    }
    return null;
  }

  getAxes() {
    return _.extend(super.getAxes(), {
      z: this.getAxis(this.args.zAxis, "z"),
      w: this.args.highlightAxis && this.getAxis(this.args.highlightAxis, "w"),
    });
  }

  rawDataToChartData(axes, rawData) {
    return {
      x: _.pluck(rawData.data, "x"),
      y: _.pluck(rawData.data, "y"),
      z: _.pluck(rawData.data, "z"),
      observation_ids: _.pluck(rawData.data, "o_id"),
      type: "scatter3d",
      mode: rawData.mode,
      text: _.pluck(rawData.data, "text"),
      hoverinfo: "text",
      marker: _.extend(
        {
          size: 7,
          color: rawData.color,
          line: {
            // NOTE: width != 0 or width != 1 does not work on some hardware
            // https://github.com/plotly/plotly.js/issues/3796
            width: 1,
          },
        },
        rawData.marker,
        axes.w && rawData.plot.highlight
          ? _.extend(
              {color: _.pluck(rawData.data, "w")},
              {
                cmin: rawData.cmin,
                cmax: rawData.cmax,
                colorscale: rawData.colorscale,
                showscale: true,
                colorbar: this.escapeTitles(
                  {
                    title: axes.w.layout.title,
                    titleside: "top",
                    ypad: 30,
                    showexponent: "all",
                    exponentformat: "e",
                  },
                  true,
                ),
              },
              rawData.plot.highlight,
            )
          : {},
      ),
    };
  }

  getChartLayout(axes, experiment, rawDataList) {
    const layout = this.args.layout || {};
    return {
      scene: _.extend(
        _.object(
          _.map(["x", "y", "z"], (ax) => [
            `${ax}axis`,
            _.extend(
              {
                backgroundcolor: CHART_COLORS.MEDIUM_GREY,
                showbackground: true,
                tickfont: {
                  family: FONT_FAMILY,
                  size: TICK_FONT_SIZE,
                  color: CHART_COLORS.FONT,
                },
                titlefont: {
                  family: FONT_FAMILY,
                  size: FONT_SIZE,
                  color: CHART_COLORS.FONT,
                },
              },
              layout[`${ax}axis`],
              axes[ax].getLayoutFromExperiment(experiment, rawDataList),
            ),
          ]),
        ),
        {
          aspectmode: "manual",
          aspectratio: {
            x: 1,
            y: 1,
            z: 1,
          },
          camera: {
            eye: {
              x: 1.75,
              y: 1.75,
              z: 1.75,
            },
          },
        },
      ),
      paper_bgcolor: "rgba(0,0,0,0)",
      margin: {
        t: 0,
        l: axes.w ? 15 : 50,
        b: 0,
      },
    };
  }

  getColorScaleBoundsFromRawDataList(rawDataList) {
    const w = _.flatten(
      _.map(rawDataList, (rawData) => _.pluck(rawData.data, "w")),
      true,
    );
    return {
      cmin: _.min(w),
      cmax: _.max(w),
    };
  }

  getColorScaleFromExperiment(experiment) {
    if (
      this.args.highlightAxis &&
      _.contains(
        [
          AxisTypes.OPTIMIZED_METRIC,
          AxisTypes.CONSTRAINED_METRIC,
          AxisTypes.STORED_METRIC,
        ],
        this.args.highlightAxis.type,
      )
    ) {
      const metric = ui.findMetric(experiment, this.args.highlightAxis.key);
      return {
        colorscale: ui.metricObjectiveOption(metric, {
          minimize: CHART_COLORS.METRIC_GRADIENT_MINIMIZED,
          maximize: CHART_COLORS.METRIC_GRADIENT,
        }),
      };
    }
    return {colorscale: CHART_COLORS.METRIC_GRADIENT};
  }

  rawDataListToChartArgs(axes, experiment, rawDataList) {
    const colorScaleBounds =
      this.getColorScaleBoundsFromRawDataList(rawDataList);
    const colorScale = this.getColorScaleFromExperiment(experiment);
    return _.extend(
      super.rawDataListToChartArgs(
        axes,
        experiment,
        _.map(rawDataList, (rawData) =>
          _.extend(rawData, colorScaleBounds, colorScale),
        ),
      ),
      {
        options: {
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: [
            "sendDataToCloud",
            "toImage",
            "resetCameraLastSave3d",
            "hoverClosest3d",
          ],
        },
      },
    );
  }
}

export default ScatterPlot4D;
