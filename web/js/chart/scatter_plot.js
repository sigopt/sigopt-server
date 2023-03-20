/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Chart from "./chart";
import {CHART_COLORS} from "./constants";
import {isDefinedAndNotNull} from "../utils";

class ScatterPlot extends Chart {
  defaultAxisLayout() {
    return {
      autorange: true,
      showgrid: true,
      zeroline: false,
    };
  }

  defaultXAxisLayout() {
    return this.defaultAxisLayout();
  }

  defaultYAxisLayout() {
    return this.defaultAxisLayout();
  }

  getDataFromObservation(axes, plot, o, obsToRunMap) {
    const xValue = axes.x.getDataFromObservation(o);
    const yValue = axes.y.getDataFromObservation(o);
    const defaultText = this.observationChartText(o, axes, obsToRunMap);
    let text = null;
    if (!plot.noText) {
      text = plot.getText
        ? plot.getText(o, defaultText, obsToRunMap)
        : defaultText;
    }
    if (isDefinedAndNotNull(xValue) && isDefinedAndNotNull(yValue)) {
      return {
        x: xValue,
        error_x: axes.x.getStddevFromObservation(o),
        y: yValue,
        error_y: axes.y.getStddevFromObservation(o),
        text: text,
        o_id: o.id,
      };
    }
    return null;
  }

  getAxes() {
    return {
      x: this.getAxis(this.args.xAxis, "x"),
      y: this.getAxis(this.args.yAxis, "y"),
    };
  }

  rawDataToChartData(axes, rawData) {
    return {
      x: _.pluck(rawData.data, "x"),
      error_x: {
        type: "data",
        value: _.pluck(rawData.data, "error_x"),
        visible: true,
        color: rawData.color,
        thickness: 1,
      },
      y: _.pluck(rawData.data, "y"),
      error_y: {
        type: "data",
        value: _.pluck(rawData.data, "error_y"),
        visible: true,
        color: rawData.color,
        thickness: 1,
      },
      observation_ids: _.pluck(rawData.data, "o_id"),
      name: rawData.plotName,
      text: _.pluck(rawData.data, "text"),
      hoverinfo: "text",
      type: "scatter",
      mode: rawData.mode,
      marker: _.extend(
        {
          size: 7,
          color: rawData.color,
          symbol: "circle",
        },
        rawData.marker,
      ),
    };
  }

  getChartLayout(axes, experiment, rawDataList) {
    const layout = this.args.layout || {};
    return _.extend({}, layout, {
      showlegend: this.args.showLegend,
      xaxis: _.extend(
        this.defaultXAxisLayout(),
        layout.xaxis,
        axes.x.getLayoutFromExperiment(experiment, rawDataList),
      ),
      yaxis: _.extend(
        this.defaultYAxisLayout(),
        layout.yaxis,
        axes.y.getLayoutFromExperiment(experiment, rawDataList),
      ),
    });
  }

  rawDataListToChartArgs(axes, experiment, rawDataList) {
    return {
      data: _.map(rawDataList, (rawData) =>
        this.rawDataToChartData(axes, rawData),
      ),
      layout: this.getChartLayout(axes, experiment, rawDataList),
    };
  }

  getChartArgs(experiment, ...observationsList) {
    const axes = this.getAxes();
    const rawDataList = _.chain(_.zip(observationsList, this.args.plots))
      .map(([observations, plot]) => {
        const data = _.chain(observations)
          .map((o) =>
            this.getDataFromObservation(
              axes,
              plot,
              o,
              this.args.observationToRunMap,
            ),
          )
          .without(null)
          .value();
        return {
          data: data,
          color: plot.color || CHART_COLORS.BLUE,
          mode: plot.mode || "markers",
          marker: plot.marker,
          plotName: plot.plotName,
          plot: plot,
        };
      })
      .value();
    return this.rawDataListToChartArgs(axes, experiment, rawDataList);
  }
}

export default ScatterPlot;
