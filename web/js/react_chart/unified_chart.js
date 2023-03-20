/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import {upperFirst} from "lodash";

import ReactChart from "./react_chart";
import ScatterPlot from "../chart/scatter_plot";
import ScatterPlot4D from "../chart/scatter_plot_4d";
import byNaturalSortName from "../experiment/sort_params";
import layout from "./layout";
import ui from "../experiment/ui";
import {
  AxisOrder,
  ChartTypes,
  PlotlyAxisScales,
  axisDefaultsProp,
  chartTypesProp,
} from "./unified_constants";
import {AxisTypes, CHART_COLORS} from "../chart/constants";
import {
  UnifiedAxisSelector,
  UnifiedChartTypeSelector,
  UnifiedCheckboxSelector,
} from "./unified_selectors";
import {isDefinedAndNotNull} from "../utils";
import {unifiedChartArgsProp} from "./unified_chart_args";
import {updateLayoutForScale} from "../chart/scale_selector";
import {updateLayoutForThresholds} from "../chart/thresholds";

const axisOptions = AxisOrder.DEFAULT;
const axisOptionsProp = PropTypes.arrayOf(PropTypes.oneOf(axisOptions));

const chartTypeOptions = _.values(ChartTypes);

export class UnifiedChart extends React.Component {
  static propTypes = {
    args: unifiedChartArgsProp.isRequired,
    axisOptions: axisOptionsProp,
    chartType: chartTypesProp,
    chartTypeOptions: PropTypes.arrayOf(chartTypesProp),
    hiddenAxisSelectors: PropTypes.arrayOf(
      PropTypes.oneOf(["x", "y", "z", "highlight"]).isRequired,
    ),
    hideAxisSelectors: PropTypes.bool,
    hideBestAssignments: PropTypes.bool,
    hideBestAssignmentsSelector: PropTypes.bool,
    hideChartTypeSelector: PropTypes.bool,
    hideFailures: PropTypes.bool,
    hideFailuresSelector: PropTypes.bool,
    hideFullCostObservations: PropTypes.bool,
    hideUnsatisfiedObservations: PropTypes.bool,
    highlightAxisOptions: axisOptionsProp,
    onClickHandler: PropTypes.func,
    showLegend: PropTypes.bool,
    showMetricThresholds: PropTypes.bool,
    xAxisDefault: axisDefaultsProp,
    xAxisOptions: axisOptionsProp,
    yAxisDefault: axisDefaultsProp,
    yAxisOptions: axisOptionsProp,
    zAxisOptions: axisOptionsProp,
  };

  state = (() => {
    const args = this.props.args;
    const finalAxisOptions = this.props.axisOptions || axisOptions;
    const createExpAxisOpt = (lst, type) =>
      _.chain(lst)
        .map((name) => ({
          key: name,
          label: name || upperFirst(type),
          type: type,
        }))
        .value();
    const getNames = (objList) =>
      _.pluck(_.clone(objList).sort(byNaturalSortName), "name");
    const typeOptions = {
      [AxisTypes.PARAMETER]: getNames(args.experiment.parameters),
      [AxisTypes.METADATA]: args.metadataKeys,
      [AxisTypes.OPTIMIZED_METRIC]: getNames(
        ui.optimizedMetrics(args.experiment),
      ),
      [AxisTypes.CONSTRAINED_METRIC]: getNames(
        ui.constrainedMetrics(args.experiment),
      ),
      [AxisTypes.STORED_METRIC]: getNames(ui.storedMetrics(args.experiment)),
    };
    let optionList = Array.prototype.concat.apply(
      [],
      _.map(finalAxisOptions, (type) => {
        const lst = typeOptions[type];
        if (lst) {
          return createExpAxisOpt(lst, type);
        }
        return [];
      }),
    );
    const finalChartTypeOptions = _.filter(
      this.props.chartTypeOptions || chartTypeOptions,
      (type) => type.axesCount <= optionList.length,
    );
    const zOptions = this.props.zAxisOptions || finalAxisOptions;
    const initialState = _.extend({
      xAxis: this.props.xAxisDefault || {},
      xOptions: this.props.xAxisOptions || finalAxisOptions,
      xScale: PlotlyAxisScales.DEFAULT,
      yAxis: this.props.yAxisDefault || {},
      yOptions: this.props.yAxisOptions || finalAxisOptions,
      yScale: PlotlyAxisScales.DEFAULT,
      zAxis: {},
      zOptions,
      zScale: PlotlyAxisScales.DEFAULT,
      highlightAxis: {},
      highlightOptions: this.props.highlightAxisOptions || zOptions,
      chartType:
        this.props.chartType &&
        this.props.chartType.axesCount <= optionList.length
          ? this.props.chartType
          : _.first(finalChartTypeOptions),
      chartTypeOptions: finalChartTypeOptions,
      showBestAssignments: !this.props.hideBestAssignments,
      showFullCostObservations: !this.props.hideFullCostObservations,
      showFailures: !this.props.hideFailures,
    });
    _.each(["x", "y", "z"], (axisName) => {
      const axis = initialState[`${axisName}Axis`];
      if (_.isEmpty(axis)) {
        const axisTypeOptions = initialState[`${axisName}Options`];
        const bestOpt = _.chain(axisTypeOptions)
          .map((type) => _.find(optionList, (opt) => opt.type === type))
          .filter(isDefinedAndNotNull)
          .first()
          .value();
        if (bestOpt) {
          _.extend(axis, bestOpt);
          optionList = _.without(optionList, bestOpt);
        }
      }
    });
    initialState.highlightAxis = _.extend({}, initialState.zAxis);
    return initialState;
  })();

  onSelectAxis = _.chain(["x", "y", "z", "highlight"])
    .map((axisName) => [
      axisName,
      (key, type) =>
        this.setState({
          [`${axisName}Axis`]: {
            key,
            label: key,
            type,
          },
          [`${axisName}Scale`]: PlotlyAxisScales.DEFAULT,
        }),
    ])
    .object()
    .value();

  onSelectScale = _.chain(["x", "y", "z"])
    .map((axisName) => [
      axisName,
      (logScaleSelected) =>
        this.setState({
          [`${axisName}Scale`]: logScaleSelected
            ? PlotlyAxisScales.LOG
            : PlotlyAxisScales.DEFAULT,
        }),
    ])
    .object()
    .value();

  render() {
    const isScatter3D = _.contains(
      [ChartTypes.Scatter3D, ChartTypes.Scatter3DWithHighlight],
      this.state.chartType,
    );
    const plots = [
      {
        mode: "markers",
        marker: {
          color: CHART_COLORS.RED,
          size: 3,
        },
        getText: (o, def) => `Failure<br />${def}`,
      },
      {
        mode: "markers",
        marker: {
          color: CHART_COLORS.GREY,
        },
        getText: (o, def) => `Did not satisfy thresholds<br />${def}`,
      },
      {
        mode: "markers",
        highlight: {},
        marker: {
          size: 9,
        },
        getText: (o, def) => `Full Cost Observation <br />${def}`,
        plotName: "Full Cost",
      },
      {
        mode: "markers",
        highlight: {},
        marker: this.state.showFullCostObservations && {
          opacity: isScatter3D ? 0.5 : 1,
          color: isScatter3D ? CHART_COLORS.BLUE : CHART_COLORS.GREY,
          size: 6,
        },
        plotName: this.state.showFullCostObservations ? "Partial Cost" : null,
      },
      {
        mode: "markers",
        marker: {
          color: CHART_COLORS.ORANGE,
        },
        getText: (o, def, obsToRunMap) => {
          const run = obsToRunMap && obsToRunMap[o.id];
          if (run) {
            return `Best Run<br />${def}`;
          }
          return `Best Assignment<br />${def}`;
        },
      },
    ];

    let succesfulObservations = this.props.hideUnsatisfiedObservations
      ? this.props.args.notFailures
      : this.props.args.successfulObservations;
    if (this.state.showBestAssignments) {
      succesfulObservations =
        this.props.args.successfulObservationsLessBestAssignments;
    }
    if (this.state.showFullCostObservations) {
      succesfulObservations =
        this.props.args.successfulObservationsLessFullCost;
    }

    const chartData = [
      this.props.args.experiment,
      this.state.showFailures ? this.props.args.failures : [],
      this.props.args.unsuccessfulObservations,
      this.state.showFullCostObservations && this.props.args.fullCostTask
        ? this.props.args.successfulObservationsByTaskName[
            this.props.args.fullCostTask.name
          ]
        : [],
      succesfulObservations,
      this.state.showBestAssignments ? this.props.args.bestAssignments : [],
    ];
    const experiment = this.props.args.experiment;
    const shouldShowSelector = (axis) => {
      if (
        this.props.hideAxisSelectors ||
        _.contains(this.props.hiddenAxisSelectors, axis)
      ) {
        return false;
      }
      const options = this.state[`${axis}Options`];
      return (
        _.chain([
          [AxisTypes.PARAMETER, _.size(experiment.parameters)],
          [AxisTypes.OPTIMIZED_METRIC, _.size(ui.optimizedMetrics(experiment))],
          [
            AxisTypes.CONSTRAINED_METRIC,
            _.size(ui.constrainedMetrics(experiment)),
          ],
          [AxisTypes.STORED_METRIC, _.size(ui.storedMetrics(experiment))],
          [AxisTypes.METADATA, _.size(this.props.args.metadataKeys)],
        ])
          .filter(([type]) => _.contains(options, type))
          .pluck(1)
          // sum
          .reduce((memo, num) => memo + num, 0)
          .value() > 1
      );
    };
    const chartLayout = {};
    if (this.props.showMetricThresholds) {
      updateLayoutForThresholds(
        this.props.args.experiment,
        this.props.args.observations,
        {xAxis: this.state.xAxis, yAxis: this.state.yAxis},
        chartLayout,
      );
    }
    updateLayoutForScale(
      {
        xaxis: this.state.xScale,
        yaxis: this.state.yScale,
        zaxis: this.state.zScale,
      },
      chartLayout,
    );

    const showXAxis = shouldShowSelector("x");
    const showYAxis = shouldShowSelector("y");
    const hasZAxis = this.state.chartType !== ChartTypes.Scatter2D;
    const showZAxis = hasZAxis && shouldShowSelector("z");
    const hasHighlightAxis =
      this.state.chartType === ChartTypes.Scatter3DWithHighlight;
    const showHighlightAxis =
      hasHighlightAxis && shouldShowSelector("highlight");
    return (
      <div className="unified-chart">
        <ReactChart
          args={{
            plots: plots,
            data: chartData,
            layout: _.extend({}, layout, chartLayout),
            showLegend: this.props.showLegend,
            xAxis: this.state.xAxis,
            yAxis: this.state.yAxis,
            zAxis: hasZAxis ? this.state.zAxis : null,
            highlightAxis: hasHighlightAxis ? this.state.highlightAxis : null,
            onClickHandler: this.props.onClickHandler,
            observationToRunMap: this.props.args.observationToRunMap,
          }}
          cls={
            this.state.chartType === ChartTypes.Scatter2D
              ? ScatterPlot
              : ScatterPlot4D
          }
        />
        <div className="param-select-holder">
          {this.props.hideChartTypeSelector || (
            <UnifiedChartTypeSelector
              onSelect={(type) => this.setState({chartType: type})}
              options={this.state.chartTypeOptions}
              selected={this.state.chartType}
            />
          )}
          {_.map(
            [
              ["x", showXAxis],
              ["y", showYAxis],
              ["z", showZAxis],
              ["highlight", showHighlightAxis],
            ],
            ([axisName, showAxis]) =>
              showAxis && (
                <UnifiedAxisSelector
                  args={this.props.args}
                  key={axisName}
                  logScaleSelected={
                    this.state[`${axisName}Scale`] === PlotlyAxisScales.LOG
                  }
                  name={axisName}
                  onSelect={this.onSelectAxis[axisName]}
                  onSelectScale={this.onSelectScale[axisName]}
                  options={this.state[`${axisName}Options`]}
                  selected={this.state[`${axisName}Axis`].label}
                />
              ),
          )}
          {this.props.hideBestAssignmentsSelector || (
            <UnifiedCheckboxSelector
              checked={this.state.showBestAssignments}
              label="best assignments"
              onChange={() =>
                this.setState((prevState) => ({
                  showBestAssignments: !prevState.showBestAssignments,
                }))
              }
            />
          )}
          {this.props.hideFailuresSelector || (
            <UnifiedCheckboxSelector
              checked={this.state.showFailures}
              label="failures"
              onChange={() =>
                this.setState((prevState) => ({
                  showFailures: !prevState.showFailures,
                }))
              }
            />
          )}
        </div>
      </div>
    );
  }
}
