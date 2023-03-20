/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {CheckpointDefaultStateBuilder} from "../widgets/checkpoints_widget/state";
import {MultiScatterMetricParameterStateBuilder} from "../widgets/multi_scatter_widget/state";
import {PCChartProjectStateBuilder} from "../widgets/pc_chart_widget/state";
import {RunTableStateBuilder} from "../widgets/runs_table_widget/state";

export const SIGOPT_DEFAULT_DASHBOARD_USER_TOKEN = "__SIGOPT_CREATED_DASHBOARD";

const dashboardLayoutBuilder = (widgets) => {
  let currentX = 0;
  let currentY = 0;
  let nextX = 0;
  let nextY = 0;
  const maxW = 2;
  const withCorrectLayout = _.map(widgets, (widget) => {
    const rightX = nextX + widget.layout.w;
    if (rightX <= maxW) {
      currentX = nextX;
      nextX = rightX;
      nextY = _.max([nextY, currentY + widget.layout.h]);
    } else {
      currentY = nextY;
      currentX = 0;
      nextX = widget.layout.w;
      nextY = currentY + widget.layout.h;
    }
    widget.layout.x = currentX;
    widget.layout.y = currentY;
    return widget;
  });

  return _.object(Object.entries(withCorrectLayout));
};

const lazyCreatedDashboardBuilder = (name, filterModel, builder) => ({
  name,
  filterModel,
  builder,
});

const activeDashboardStateBuilder = (widgets, filterModel, name) => {
  const validWidgets = _.filter(widgets, Boolean);
  const initialLayout = dashboardLayoutBuilder(validWidgets);
  const nextWidgetId = Object.entries(initialLayout).length;

  return {
    version: 1,
    widgets: initialLayout,
    nextWidgetId,
    filterModel,
    user: SIGOPT_DEFAULT_DASHBOARD_USER_TOKEN,
    name,
  };
};

const defaultProjectDashboard = (runs, dimensions, dashboard) => {
  const defaultMultiScatterWidget =
    MultiScatterMetricParameterStateBuilder(dimensions);
  const defaultPCChart = PCChartProjectStateBuilder(dimensions);
  const defaultRunTable = RunTableStateBuilder("Runs");
  const checkpointsWidget = CheckpointDefaultStateBuilder(runs);

  const defaultProjectWidgets = [
    checkpointsWidget,
    defaultMultiScatterWidget,
    defaultPCChart,
    defaultRunTable,
  ];

  return activeDashboardStateBuilder(
    defaultProjectWidgets,
    dashboard.filterModel,
    dashboard.name,
  );
};

export const createDefaultProjectDashboard = () =>
  lazyCreatedDashboardBuilder(
    "Default Project Dashboard",
    {},
    defaultProjectDashboard,
  );

const defaultDashboard = (runs, dimensions, dashboard) => {
  const defaultMultiScatterWidget =
    MultiScatterMetricParameterStateBuilder(dimensions);
  const defaultPCChart = PCChartProjectStateBuilder(dimensions);
  const defaultRunTable = RunTableStateBuilder("Runs");

  const checkpointsWidget = CheckpointDefaultStateBuilder(runs);

  const defaultRunWidgets = [
    checkpointsWidget,
    defaultPCChart,
    defaultMultiScatterWidget,
    defaultRunTable,
  ];

  return activeDashboardStateBuilder(
    defaultRunWidgets,
    dashboard.filterModel,
    dashboard.name,
  );
};

export const createDefaultModelDashboard = (modelType) =>
  lazyCreatedDashboardBuilder(
    `Model: ${modelType}`,
    {key: "model.type", value: modelType},
    defaultDashboard,
  );

export const createDefaultExperimentDashboard = (experimentId) =>
  lazyCreatedDashboardBuilder(
    `Experiment: ${experimentId}`,
    {key: "experiment", value: experimentId},
    defaultDashboard,
  );
