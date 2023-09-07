/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import $ from "jquery";
import _ from "underscore";
import Plotly from "plotly.js-strict-dist";
import Spinner from "spin.js";
import escape from "escape-html";

import ui from "../experiment/ui";
import {AxisTypes} from "./constants";
import {ParameterTransformations} from "../experiment/constants";
import {axisValueGetter, axisValueStddevGetter} from "./values";
import {getChartRange} from "./range";
import {isDefinedAndNotNull, isJsObject} from "../utils";

const recursivelyMerge = function (...args) {
  return _.reduce(args, (a, b) => $.extend(true, a, b || {}), {});
};

class Chart {
  constructor(config) {
    this.$el = $(config.el);
    this.$chart = this.$el.find(".chart");
    this.setArgs(config);
    this.isDrawn = false;
  }

  get chartDiv() {
    return this.$chart[0];
  }

  get hoverLayer() {
    // Lazy initialization of drag layer, since it needs to be drawn first
    // Otherwise the `unhover` handler is triggered right away
    // HACK: .draglayer doesn't work for ScatterPlot4d, so search for
    // a canvas first
    const canvasLayer = this.$chart.find("canvas")[0];
    const dragLayer = canvasLayer ? null : this.$chart.find(".draglayer")[0];
    return canvasLayer || dragLayer;
  }

  resizeHandler = _.throttle(() => {
    this.forceRedrawChart();
  }, 100);

  initialize() {
    const spinner = new Spinner().spin();
    this.$chart.append(spinner.el);
    this.scrollHandler = _.throttle(_.bind(this.maybeRedrawChart, this), 100);
    $(window).on("scroll", this.scrollHandler);
    $(window).on("resize", this.resizeHandler);
    this.redrawChart();
  }

  plotlyClick = (event, data) => {
    if (this.onClickHandler) {
      this.onClickHandler(data);
    }
  };

  plotlyHover = (event, data) => {
    if (this.onClickHandler && this.hoverLayer) {
      this.hoverLayer.style.cursor = "pointer";
    }
    if (this.onHoverHandler) {
      this.onHoverHandler(data);
    }
  };

  plotlyUnhover = (event, data) => {
    if (this.onClickHandler && this.hoverLayer) {
      this.hoverLayer.style.cursor = "";
    }
    if (this.onUnhoverHandler) {
      this.onUnhoverHandler(data);
    }
  };

  setupHandlers() {
    const $chartDiv = $(this.chartDiv);
    $chartDiv.off("plotly_click", this.plotlyClick);
    $chartDiv.off("plotly_hover", this.plotlyHover);
    $chartDiv.off("plotly_unhover", this.plotlyUnhover);
    $chartDiv.on("plotly_click", this.plotlyClick);
    $chartDiv.on("plotly_hover", this.plotlyHover);
    $chartDiv.on("plotly_unhover", this.plotlyUnhover);
  }

  setArgs(args) {
    this.args = args;
    this.data = args.data;
    this.layout = args.layout || {};
    this.options = {
      showLink: false,
      displayModeBar: false,
    };
    this.onClickHandler = args.onClickHandler;
  }

  // Method for generating a helpful axis object from
  // info passed in
  getAxis(axis, axisLetter) {
    const layout = {
      title: axis && axis.label,
      showexponent: "all",
      exponentformat: "e",
    };
    return {
      extra: axis && axis.extra,
      label: axis && axis.label,
      type: axis && axis.type,
      layout: layout,
      getDataFromObservation: axis ? this.valueGetter(axis) : _.noop,
      getStddevFromObservation:
        axis && axis.stddev ? this.valueStddevGetter(axis) : _.noop,
      getLayoutFromExperiment: (experiment, rawDataList) => {
        const experimentLayout = _.extend({}, layout);
        if (axis && axis.type === AxisTypes.PARAMETER && axis.label) {
          const parameter = _.find(
            experiment.parameters,
            (p) => p.name === axis.label,
          );
          if (parameter && parameter.bounds) {
            const filteredValues = _.chain(rawDataList)
              .pluck("data")
              .flatten(true)
              .pluck(axisLetter)
              .filter(isDefinedAndNotNull)
              .value();
            const getBound = (value, agg) =>
              agg(_.flatten([filteredValues, [value]], true));
            _.extend(experimentLayout, {
              autorange:
                parameter.transformation === ParameterTransformations.LOG,
              range: getChartRange(
                getBound(parameter.bounds.min, _.min),
                getBound(parameter.bounds.max, _.max),
              ),
            });
          }
        }
        return experimentLayout;
      },
    };
  }

  valueGetter = axisValueGetter;

  valueStddevGetter = axisValueStddevGetter;

  objectToChartText(obj) {
    return _.chain(obj)
      .pairs()
      .sortBy((d) => d[0])
      .map((d) => `${d[0]}: ${d[1]}`)
      .value()
      .join("<br />");
  }

  observationChartText(observation, axes, obsToRunMap) {
    const axisOrder = ["x", "y", "z", "w"];
    const sortedAxes = _.chain(axes)
      .pairs()
      .groupBy((p) => `${p[1].type}${p[1].label}`)
      .map((grouped) => {
        const byAxis = _.indexBy(grouped, ([key]) => key);
        return _.chain(axisOrder)
          .map((key) => byAxis[key])
          .filter()
          .first()
          .value();
      })
      .sortBy(0)
      .pluck(1)
      .value();
    let topText = `Observation ID: ${observation.id}`;
    if (obsToRunMap && obsToRunMap[observation.id]) {
      const runId = obsToRunMap[observation.id];
      topText = `Run ID: ${runId}`;
    }
    return _.chain([
      [topText],
      observation.task
        ? [
            [`Task Name: ${observation.task.name}`],
            [`Task Cost: ${ui.renderTaskCost(observation.task.cost)}`],
          ]
        : [],
      _.chain(sortedAxes)
        .map((axis) => [axis.getDataFromObservation(observation), axis])
        .filter(([value]) => isDefinedAndNotNull(value))
        .map(([value, axis]) => `${axis.label}: ${value}`)
        .value(),
    ])
      .flatten(true)
      .value()
      .join("<br />");
  }

  defaultChartArgs() {
    return {
      data: [],
      layout: {
        hovermode: "closest",
        showlegend: false,
      },
      options: {responsive: true},
    };
  }

  // Overridden by base classes
  getChartArgs() {
    return {};
  }

  destroy() {
    $(window).off("scroll", this.scrollHandler);
    $(window).off("resize", this.resizeHandler);
  }

  maybeRedrawChart() {
    if (!this.isDrawn) {
      this.redrawChart();
    }
  }

  redrawChart() {
    const {data, layout, options} = this._plotlyArgs(...this.data);
    if (data) {
      this.drawChart(data, layout, options);
    }
    this.setupHandlers();
  }

  forceRedrawChart() {
    const {data, layout, options} = this._plotlyArgs(...this.data);
    if (data) {
      this.newChart(data, layout, options);
    }
  }

  newChart(data, layout, options) {
    this.$chart.empty();
    try {
      Plotly.newPlot(this.$chart[0], data, layout, options);
    } catch (e) {
      console.error(e); // eslint-disable-line no-console
      this.$chart.empty();
      this.$chart.append(
        $("<p>").text(
          "Unfortunately, we cannot render this chart in your browser at the present time.",
        ),
      );
    }
    this.isDrawn = true;
  }

  updateChart(data, providedLayout) {
    // TODO: This can be more efficient by detecting changes and only calling
    // relayout or deleteTraces/addTraces. Probably not worth worrying about right now
    const chartDiv = this.chartDiv;
    const chartLayout = chartDiv.layout || {};

    // For 3d charts, preserve the user's "view"
    const matchingLayout = recursivelyMerge(
      {},
      providedLayout,
      chartLayout.scene
        ? {
            scene: {
              aspectratio: chartLayout.scene.aspectratio,
              camera: chartLayout.scene.camera,
            },
          }
        : null,
    );

    const sceneHasChanged =
      chartLayout.scene &&
      matchingLayout.scene &&
      !_.isEqual(chartLayout.scene, matchingLayout.scene);

    // NOTE: Plotly is super finicky about reapplying layout. It resets the whole
    // graph (including any user input) so this is something we want to do rarely. So we
    // will assume we only do it if we need to change the bounds of the graph. So, we will
    // say that each axis is unchanged if...
    const axisMatches = (name) => {
      const hasAxis = matchingLayout[name] || chartLayout[name];
      const rangeMatches =
        // The axis is undefined for this graph, or...
        !hasAxis ||
        // The range is not specified, or...
        !matchingLayout[name].range ||
        !chartLayout[name].range ||
        // The range is specified but it is unchanged
        _.isEqual(matchingLayout[name].range, chartLayout[name].range);

      const nameMatches =
        !hasAxis ||
        matchingLayout[name].title === (chartLayout[name].title || {}).text;

      return Boolean(rangeMatches && nameMatches);
    };

    const annotationsMatch = _.every(
      _.zip(matchingLayout.annotations, chartLayout.annotations),
      (a) => a[0].text === a[1].text,
    );

    const shouldRelayout =
      !chartLayout ||
      !annotationsMatch ||
      !axisMatches("xaxis") ||
      !axisMatches("yaxis") ||
      !axisMatches("zaxis") ||
      sceneHasChanged;

    chartDiv.data = data;
    Plotly.redraw(chartDiv).then(() => {
      if (shouldRelayout) {
        Plotly.relayout(chartDiv, matchingLayout);
      }
    });
    this.isDrawn = true;
  }

  drawChart(data, layout, options) {
    if (this.isDrawn) {
      this.updateChart(data, layout);
    } else {
      this.newChart(data, layout, options);
    }
  }

  restyle(option, value) {
    Plotly.restyle(this.chartDiv, option, value);
  }

  _plotlyArgs() {
    const defaultArgs = this.defaultChartArgs();
    const chartArgs = this.getChartArgs(...this.data) || {};
    const mergedArgs = recursivelyMerge(defaultArgs, chartArgs);
    const {data, layout, options} = mergedArgs;
    return {
      data: data,
      layout: this.escapeTitles(recursivelyMerge(this.layout, layout), true),
      options: recursivelyMerge(this.options, options),
    };
  }

  escapeTitles(obj, bold) {
    const escapeTitle = (t) => (bold ? `<b>${escape(t)}</b>` : escape(t));
    if (isJsObject(obj)) {
      if (obj.title) {
        if (isJsObject(obj.title) && obj.title.text) {
          obj.title.text = escapeTitle(obj.title.text);
        } else {
          obj.title = escapeTitle(obj.title);
        }
      }
      _.mapObject(obj, (v, k) => this.escapeTitles(v, bold && k !== "scene"));
    }
    return obj;
  }
}

export default Chart;
