/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import Plotly from "plotly.js-strict-dist";

import Chart from "./chart";
import layout from "../react_chart/layout";
import {CHART_COLORS} from "./constants";
import {
  CHECKPOINT_AXIS,
  TrainingRunsAxisOptions,
  createAxis,
  metricAxisOption,
} from "./training_runs_axis";
import {isDefinedAndNotNull, renderNumber} from "../utils";

const getPlotlyAxis = (axis, number) =>
  number > 0 ? `${axis}${number + 1}` : axis;

const largePrime = 7919;

const getRunIdAndIndex = (point) => {
  const {globalIndex, runId} = point.data;
  const selectedIndex = globalIndex[point.pointNumber];
  return [runId, selectedIndex];
};

export default class MpmCheckpointsChart extends Chart {
  getChartData(trainingRuns, checkpointsByRunId, metricNames) {
    const runsAndCheckpoints = _.map(trainingRuns, (trainingRun) => ({
      checkpoints: checkpointsByRunId[trainingRun.id],
      trainingRun,
    }));
    const numCheckpoints = _.chain(runsAndCheckpoints)
      .pluck("checkpoints")
      .map(_.size)
      .max()
      .value();
    const xAxis = createAxis(
      TrainingRunsAxisOptions[CHECKPOINT_AXIS],
      numCheckpoints,
      runsAndCheckpoints,
    );
    const yAxes = _.map(metricNames, (metricName) =>
      createAxis(
        metricAxisOption(metricName),
        numCheckpoints,
        runsAndCheckpoints,
      ),
    );
    return {
      xAxis,
      yAxes,
      chartData: _.chain(yAxes)
        .map((yAxis, axisNumber) =>
          _.chain(runsAndCheckpoints)
            .filter(({checkpoints}) => _.size(checkpoints) > 0)
            .map(({trainingRun, checkpoints}) => {
              const runId = trainingRun.id;
              const unfilteredCheckpointTrace = _.chain(checkpoints)
                .map((checkpoint, globalIndex) => {
                  const ordinal = globalIndex + 1;
                  const [xData, yData] = _.map([xAxis, yAxis], (axis) => {
                    const value = axis.getCheckpointValue(
                      trainingRun,
                      checkpoint,
                      ordinal,
                    );
                    const renderedValue = isDefinedAndNotNull(value)
                      ? renderNumber(value, 6)
                      : null;
                    return {value, renderedValue};
                  });
                  const text = `${yAxis.layout.title}: ${yData.renderedValue}`;
                  return {
                    x: xData.value,
                    y: yData.value,
                    text,
                    globalIndex,
                    defined: _.all(
                      [xData.value, yData.value],
                      isDefinedAndNotNull,
                    ),
                  };
                })
                .value();
              const checkpointTrace = _.filter(
                unfilteredCheckpointTrace,
                "defined",
              );
              if (_.isEmpty(checkpointTrace)) {
                return null;
              }
              _.each(checkpointTrace, (point, index) => {
                point.pointNumber = index;
              });
              const nextDefinedPoints = _.chain(unfilteredCheckpointTrace)
                .reduce((rest, point) => {
                  if (point.defined) {
                    rest.push(point);
                  } else {
                    rest.push(rest[rest.length - 1]);
                  }
                  return rest;
                }, [])
                .value();
              const pointNumbers = _.chain(nextDefinedPoints)
                .filter()
                .pluck("pointNumber")
                .value();
              return {
                axisNumber,
                checkpointTrace,
                pointNumbers,
                layoutInfo: {
                  xaxis: "x",
                  yaxis: getPlotlyAxis("y", axisNumber),
                },
                runId,
              };
            })
            .filter()
            .value(),
        )
        .flatten()
        .value(),
    };
  }

  getChartArgs({checkpointsByRunId, metricNames, trainingRuns}) {
    const {xAxis, yAxes, chartData} = this.getChartData(
      trainingRuns,
      checkpointsByRunId,
      metricNames,
    );

    const getColorFromId = (runId) => {
      const palette = CHART_COLORS.CHECKPOINTS_PALETTE;
      const index = (parseInt(runId, 10) * largePrime) % _.size(palette);
      return palette[index];
    };

    const args = {
      data: _.map(
        chartData,
        (
          {axisNumber, checkpointTrace, layoutInfo, pointNumbers, runId},
          curveNumber,
        ) =>
          _.extend(
            {
              x: _.pluck(checkpointTrace, "x"),
              y: _.pluck(checkpointTrace, "y"),
              globalIndex: _.pluck(checkpointTrace, "globalIndex"),
              text: _.pluck(checkpointTrace, "text"),
              hoverinfo: "text",
              type: "scatter",
              mode: "line",
              line: {
                color: getColorFromId(runId),
                width: 1,
                opacity: 1,
              },
              axisNumber,
              curveNumber,
              pointNumbers,
              runId,
            },
            layoutInfo,
          ),
      ),
      layout: _.extend(
        {
          grid: {
            rows: _.size(metricNames),
            columns: 1,
            subplots: _.map(
              yAxes,
              (yAxis, index) => `x${getPlotlyAxis("y", index)}`,
            ),
          },
        },
        layout,
        {xaxis: xAxis.layout},
        _.chain(yAxes)
          .map((yAxis, index) => [getPlotlyAxis("yaxis", index), yAxis.layout])
          .object()
          .value(),
      ),
    };

    args.data.byRunId = _.groupBy(args.data, "runId");

    return args;
  }

  onHoverHandler(event) {
    if (_.size(event.points) !== 1) {
      return;
    }
    const [point] = event.points;
    const [runId, selectedIndex] = getRunIdAndIndex(point);
    this.hoverTraces(runId, selectedIndex);
    if (this.args.onCheckpointHover) {
      this.args.onCheckpointHover(runId, selectedIndex);
    }
  }

  onUnhoverHandler(event) {
    if (this.args.onCheckpointUnhover) {
      const unhovered = _.map(event.points, getRunIdAndIndex);
      this.args.onCheckpointUnhover(unhovered);
    }
  }

  hoverTraces(runId, selectedIndex) {
    if (!this.chartDiv || !this.chartDiv.data) {
      return;
    }
    const chartData = this.chartDiv.data;
    const traces = chartData.byRunId[runId];
    Plotly.Fx.hover(
      this.chartDiv,
      _.map(traces, ({curveNumber, pointNumbers}) => ({
        curveNumber,
        pointNumber: isDefinedAndNotNull(selectedIndex)
          ? pointNumbers[selectedIndex]
          : _.last(pointNumbers),
      })),
      _.map(traces, ({xaxis, yaxis}) => xaxis + yaxis),
    );
  }
}
