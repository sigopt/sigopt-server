/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Chart from "./chart";
import layout from "../react_chart/layout";
import ui from "../experiment/ui";
import {CHART_COLORS} from "./constants";
import {coalesce, renderNumber} from "../utils";

class TaskDistributionChart extends Chart {
  getChartData(experiment, observations, yAxis) {
    const observationCountsByTaskName = _.countBy(
      observations,
      (o) => o.task.name,
    );
    const totalBudgetConsumed = renderNumber(
      experiment.progress.observation_budget_consumed,
      true,
    );

    return _.chain(experiment.tasks)
      .sortBy((t) => t.cost)
      .reverse()
      .map((t) => {
        const taskInfo = ui.renderTask(t);
        const numObservations = coalesce(
          observationCountsByTaskName[t.name],
          0,
        );
        const budgetConsumed = numObservations * t.cost;
        const text = this.objectToChartText({
          "Budget Consumed": `${renderNumber(
            budgetConsumed,
            true,
          )}/${totalBudgetConsumed}`,
          "Observation Count": `${numObservations}/${experiment.progress.observation_count}`,
        });
        return [
          taskInfo,
          yAxis === "Budget Consumed" ? budgetConsumed : numObservations,
          text,
        ];
      })
      .unzip()
      .value();
  }

  getAxes(yAxis) {
    return {
      xaxis: _.extend({title: "Task"}, layout.xaxis),
      yaxis: _.extend({title: yAxis}, layout.yaxis),
    };
  }

  getChartArgs(experiment, observations, yAxis) {
    const chartData = this.getChartData(experiment, observations, yAxis);

    return {
      data: [
        {
          x: chartData[0],
          y: chartData[1],
          text: chartData[2],
          hoverinfo: "text",
          marker: {
            color: CHART_COLORS.BLUE,
          },
          type: "bar",
        },
      ],
      layout: _.extend({}, layout, this.getAxes(yAxis)),
    };
  }
}
export default TaskDistributionChart;
