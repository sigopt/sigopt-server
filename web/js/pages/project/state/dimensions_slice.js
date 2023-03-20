/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable no-underscore-dangle */
import _ from "underscore";
import {createSlice} from "@reduxjs/toolkit";

import _fetchRuns from "../../../training_run/fetch";
import {createDimensionsFromRuns} from "../data/dimensions";
import {isDefinedAndNotNull} from "../../../utils";

const initialDimensionsSlice = {
  allRuns: null,
  checkpointHoverInfo: {runId: null, checkpointNum: null},
  checkpointsByRunId: null,
  definedFields: null,
  dimensions: null,
  filterModel: null,
  hoverInfo: {runIndex: null, runId: null, checkpointIndex: null},
  idIndexMap: {},
  indexIdMap: {},
  runs: null,
  selectedIds: [],
  selectedIndexes: [],
  tableApi: null,
  tableFiltered: false,
  tagsById: null,
};

const _setHoverInfo = (state, {payload}) => {
  let {runIndex, runId} = payload;
  const {checkpointIndex} = payload;

  if (isDefinedAndNotNull(runId)) {
    runIndex = state.idIndexMap[runId];
  } else if (isDefinedAndNotNull(runIndex)) {
    runId = state.indexIdMap[runIndex];
  }

  state.hoverInfo = {runIndex, runId, checkpointIndex};
};

const _setSelectedIndexes = (state, {payload}) => {
  state.selectedIndexes = payload;
  state.selectedIds = _.map(payload, (index) => state.indexIdMap[index]);
};

const _setSelectedIds = (state, {payload}) => {
  state.selectedIds = payload;
  state.selectedIndexes = _.map(payload, (id) => state.idIndexMap[id]);
};

const _setTableApi = (state, {payload}) => {
  state.tableApi = payload;
};

const _toggleDimensionsToFiltered = (state) => {
  const tableFiltered = !state.tableFiltered;
  state.tableFiltered = tableFiltered;
  if (state.tableApi === null) {
    return;
  }

  let runsToUse = state.runs;
  if (tableFiltered) {
    const filteredRuns = [];
    state.tableApi.forEachNodeAfterFilter((row) => filteredRuns.push(row.data));
    runsToUse = filteredRuns;
  }

  const {dimensions, idIndexMap, indexIdMap} = createDimensionsFromRuns(
    state.definedFields,
    runsToUse,
  );
  state.dimensions = dimensions;
  state.idIndexMap = idIndexMap;
  state.indexIdMap = indexIdMap;
};

const _updateFiltered = (state) => {
  if (state.tableFiltered) {
    const filteredRuns = [];
    state.tableApi.forEachNodeAfterFilter((row) => filteredRuns.push(row.data));
    const {dimensions, idIndexMap, indexIdMap} = createDimensionsFromRuns(
      state.definedFields,
      filteredRuns,
    );
    state.dimensions = dimensions;
    state.idIndexMap = idIndexMap;
    state.indexIdMap = indexIdMap;
  }
};

const _getRunsSuccess = (state, {payload}) => {
  const {runs, definedFields, tags} = payload;

  state.runsById = {};
  _.each(runs, (run) => (state.runsById[run.id] = run));

  state.tagsById = tags;
  state.definedFields = definedFields;
  state.allRuns = runs;
  state.hasCheckpoints = _.any(runs, (run) => run.checkpoint_count > 0);
  state.hasExperiments = _.any(runs, (run) => run.experiment);
};

const _getCheckpointsSuccess = (state, {payload}) => {
  const {checkpointsByRunId} = payload;
  state.checkpointsByRunId = checkpointsByRunId;
};

const _createTagSuccess = (state, {payload}) => {
  const {newTag} = payload;
  state.tagsById = _.extend({}, state.tagsById, {[newTag.id]: newTag});
};

const _updateRunSuccess = (state, {payload}) => {
  const {updatedRun} = payload;
  state.runsById = _.extend({}, state.runsById, {[updatedRun.id]: updatedRun});
};

// TODO Hook in table api to support more complex filters
const _changeFilterModel = (state, {payload}) => {
  if (payload && payload.key) {
    if (!_.contains(["experiment", "model.type"], payload.key)) {
      throw new Error(
        "Dashboard filter models only support simple manually implemented filters",
      );
    }

    if (payload.key === "model.type") {
      state.runs = _.filter(
        state.allRuns,
        (run) => run.model && run.model.type === payload.value,
      );
    }

    if (payload.key === "experiment") {
      state.runs = _.filter(
        state.allRuns,
        (run) => run.experiment === payload.value,
      );
    }
  } else {
    state.runs = state.allRuns;
  }

  const {dimensions, idIndexMap, indexIdMap} = createDimensionsFromRuns(
    state.definedFields,
    state.runs,
  );
  state.dimensions = dimensions;
  state.idIndexMap = idIndexMap;
  state.indexIdMap = indexIdMap;
  state.filterModel = payload;
};

const _getTagsSuccess = (state, {payload}) => {
  const {tags} = payload;
  state.tagsById = _.indexBy(tags, "id");
};

const dimensionsSlice = createSlice({
  name: "dimensions",
  initialState: initialDimensionsSlice,
  reducers: {
    setSelectedIndexes: _setSelectedIndexes,
    setSelectedIds: _setSelectedIds,
    setHoverInfo: _setHoverInfo,
    setTableApi: _setTableApi,
    toggleDimensionsToFiltered: _toggleDimensionsToFiltered,
    updateFiltered: _updateFiltered,
    getRunsSuccess: _getRunsSuccess,
    getTagsSuccess: _getTagsSuccess,
    changeFilterModel: _changeFilterModel,
    getCheckpointsSuccess: _getCheckpointsSuccess,
    updateRunSuccess: _updateRunSuccess,
    createTagSuccess: _createTagSuccess,
  },
});

export const {
  setSelectedIndexes,
  setSelectedIds,
  toggleDimensionsToFiltered,
  setTableApi,
  setHoverInfo,
  updateFiltered,
  getRunsSuccess,
  changeFilterModel,
  getCheckpointsSuccess,
  getTagsSuccess,
  updateRunSuccess,
  createTagSuccess,
} = dimensionsSlice.actions;

export const DimenensionsReducer = dimensionsSlice.reducer;

export const fetchTags = () => (dispatch, getState) => {
  const state = getState();

  state.services.promiseApiClient
    .clients(state.resources.project.client)
    .tags()
    .exhaustivelyPage()
    .then((tags) => dispatch(getTagsSuccess({tags})));
};

export const fetchRuns =
  (
    success,
    error,
    experiment = null,
    organizationId = null,
    excludeArchivedRuns = false,
  ) =>
  (dispatch, getState) => {
    const state = getState();
    const needFilterDefaultParams = true;
    _fetchRuns(
      state.services.promiseApiClient,
      state.resources.project,
      experiment,
      needFilterDefaultParams,
      organizationId,
      excludeArchivedRuns,
    )
      .then(({definedFields, runs, tags}) => {
        dispatch(getRunsSuccess({definedFields, runs, tags}));
        return runs;
      })
      .then(success, error);
  };

export const fetchCheckpoints = (cb, error) => (dispatch, getState) => {
  const state = getState();
  const success = (checkpointsByRunId) => {
    dispatch(getCheckpointsSuccess({checkpointsByRunId}));
    return cb && cb(checkpointsByRunId);
  };

  if (!state.dimensions.hasCheckpoints) {
    success(
      _.chain(state.dimensions.runsById)
        .map(({id}) => [id, []])
        .object()
        .value(),
    );
    return;
  }

  Promise.all(
    _.map(state.dimensions.runsById, ({checkpoint_count, id}) =>
      checkpoint_count > 0
        ? state.services.promiseApiClient
            .trainingRuns(id)
            .checkpoints()
            .exhaustivelyPage()
            .then((checkpoints) => Promise.resolve([id, checkpoints.reverse()]))
        : [],
    ),
  )
    .then((allRunIdsAndCheckpoints) => _.object(allRunIdsAndCheckpoints))
    .then(success)
    .catch(error);
};

export const modifyRun = (runId, modifier) => (dispatch, getState) => {
  const state = getState();
  const run = state.runs.runsById[runId];

  const updatedRun = modifier(run);

  dispatch(updateRunSuccess({updatedRun}));
};

export const createTag = (tagData, success, error) => (dispatch, getState) => {
  const state = getState();

  state.services.promiseApiClient
    .clients(state.resources.project.client)
    .tags()
    .create({name: tagData.name, color: tagData.color})
    .then((newTag) => {
      dispatch(createTagSuccess({newTag}));
      return success && success(newTag);
    }, error);
};
