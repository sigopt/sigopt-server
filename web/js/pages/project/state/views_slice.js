/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import {createSlice} from "@reduxjs/toolkit";

const LOADING_STATES = {LOADING: "LOADING", LOADED: "LOADED", FAILED: "FAILED"};

const initialState = {
  views: null,
  loadingState: LOADING_STATES.LOADING,
  runViewApi: null,
  error: null,
};

const createApiBoilerplate = (state) => {
  const {project, client} = state.resources;
  const {promiseApiClient} = state.services;

  const parent_resource_id = {project: project.id, client: client.id};
  const webDataArgs = {
    parent_resource_type: "project",
    web_data_type: "ag_run_view",
    parent_resource_id,
  };

  return {
    route: promiseApiClient.webData(),
    queryBoilerplate: _.extend({}, webDataArgs, {
      parent_resource_id: JSON.stringify(parent_resource_id),
    }),
    bodyBoilerplate: _.extend({}, webDataArgs),
  };
};

const viewsSlice = createSlice({
  name: "views",
  initialState,
  reducers: {
    loadingFailed: (state, {payload}) => {
      state.loadingState = LOADING_STATES.FAILED;
      state.error = payload;
    },
    getViewsSuccess: (state, {payload}) => {
      state.views = payload;
      state.loadingState = LOADING_STATES.LOADED;
    },
  },
});

const {getViewsSuccess} = viewsSlice.actions;

export const ViewsReducer = viewsSlice.reducer;

export const fetchViews = () => (dispatch, getState) => {
  const state = getState();
  const runViewApi = createApiBoilerplate(state);
  runViewApi.route.fetch(runViewApi.queryBoilerplate).then((viewsPage) => {
    const currentUserId = (state.resources.user || {}).id;
    const [currentUserViews, restViews] = _.partition(
      viewsPage.data,
      (v) => v.created_by === currentUserId,
    );
    const payload = {currentUserViews, restViews};
    dispatch(getViewsSuccess(payload));
  });
};

export const createView = (viewName, payload) => (dispatch, getState) => {
  const state = getState();
  const runViewApi = createApiBoilerplate(state);
  const requestParams = _.extend({}, runViewApi.bodyBoilerplate, {
    payload,
    display_name: viewName,
  });
  runViewApi.route
    .create(requestParams)
    .then(setTimeout(() => dispatch(fetchViews()), 100));
};

export const deleteView = (viewId) => (dispatch, getState) => {
  const state = getState();
  const runViewApi = createApiBoilerplate(state);
  const requestParams = _.extend({}, runViewApi.queryBoilerplate, {id: viewId});
  runViewApi.route
    .delete(requestParams)
    .then(setTimeout(() => dispatch(fetchViews()), 100));
};
