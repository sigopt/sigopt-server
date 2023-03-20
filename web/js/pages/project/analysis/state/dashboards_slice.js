/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable no-underscore-dangle */
import _ from "underscore";
import {createSlice} from "@reduxjs/toolkit";

import {
  createDefaultExperimentDashboard,
  createDefaultModelDashboard,
  createDefaultProjectDashboard,
} from "../dashboard/create_dashboards";

const dashboardsInitialState = {
  dashboards: [],
  currentDashboardId: null,
};

const _createDefaultDashboards = (state, {payload}) => {
  const {allRuns} = payload;
  const projectDashboard = createDefaultProjectDashboard();

  const modelTypes = _.filter(
    _.unique(_.map(allRuns, (r) => r.model && r.model.type)),
  );
  const modelDashboards = _.map(modelTypes, (modelType) =>
    createDefaultModelDashboard(modelType),
  );

  const experimentIds = _.filter(_.unique(_.map(allRuns, (r) => r.experiment)));
  const experimentDashboards = _.map(experimentIds, (experimentId) =>
    createDefaultExperimentDashboard(experimentId),
  );

  state.dashboards = [
    projectDashboard,
    ...modelDashboards,
    ...experimentDashboards,
  ];
  state.currentDashboardId = 0;
};

const _addNewWidget = (state, {payload}) => {
  // Move everything else down slightly so auto reflow handles layout
  for (const widget of Object.values(
    state.dashboards[state.currentDashboardId].widgets,
  )) {
    if (widget.layout.y === 0) {
      widget.layout.y = 0.5;
    }
  }
  const newId = state.nextItemId;
  payload.layout.x = 0;
  payload.layout.y = 0;

  // Sanity checking w/h - react-grid-layout messes up when w/h are greater than mins
  payload.layout.w = Math.max(payload.layout.w, payload.layout.minW);
  payload.layout.h = Math.max(payload.layout.h, payload.layout.minH);

  state.dashboards[state.currentDashboardId].widgets[newId] = payload;
  state.nextItemId += 1;
};

const _updateLayouts = (state, {payload}) => {
  const newLayouts = payload;
  for (const newLayout of newLayouts) {
    const relevantLayoutData = _.pick(
      newLayout,
      "x",
      "y",
      "w",
      "h",
      "minW",
      "minH",
      "i",
    );
    state.dashboards[state.currentDashboardId].widgets[newLayout.i].layout =
      relevantLayoutData;
  }
};

const _updateWidget = (state, {payload}) => {
  const {widgetId, updateFunc} = payload;
  const widgetToBeUpdated =
    state.dashboards[state.currentDashboardId].widgets[widgetId];

  updateFunc(widgetToBeUpdated);
};

const _replaceWidget = (state, {payload}) => {
  const {widgetId, widgetData} = payload;
  const oldWidget =
    state.dashboards[state.currentDashboardId].widgets[widgetId];
  widgetData.layout.x = oldWidget.layout.x;
  widgetData.layout.y = oldWidget.layout.y;

  state.dashboards[state.currentDashboardId].widgets[widgetId] = widgetData;
};

const _deleteWidget = (state, {payload}) => {
  delete state.dashboards[state.currentDashboardId].widgets[payload];
};

const _changeDashboard = (state, {payload}) => {
  state.currentDashboardId = payload;
};

const _buildDashboard = (state, {payload}) => {
  const {runs, dimensions, dashboardId} = payload;
  const currentDashboard = state.dashboards[state.currentDashboardId];
  // Likely not needed but prevents a theoretical race condition
  if (dashboardId === state.currentDashboardId && currentDashboard.builder) {
    state.dashboards[dashboardId] = currentDashboard.builder(
      runs,
      dimensions,
      currentDashboard,
    );
  }
};

const dashboardsSlice = createSlice({
  name: "dashboards",
  initialState: dashboardsInitialState,
  reducers: {
    addNewWidget: _addNewWidget,
    updateLayouts: _updateLayouts,
    replaceWidget: _replaceWidget,
    updateWidget: _updateWidget,
    deleteWidget: _deleteWidget,
    createDefaultDashboards: _createDefaultDashboards,
    changeDashboard: _changeDashboard,
    buildDashboard: _buildDashboard,
  },
});

export const {
  addNewWidget,
  updateLayouts,
  updateWidget,
  deleteWidget,
  createDefaultDashboards,
  changeDashboard,
  buildDashboard,
  replaceWidget,
} = dashboardsSlice.actions;

export const DashboardsReducer = dashboardsSlice.reducer;
