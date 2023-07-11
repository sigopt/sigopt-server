/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import {connect} from "react-redux";

import {CheckpointsWidgetStateBuilder} from "./state";
import {DOCS_URL} from "../../../../../net/constant";
import {RunsSelect} from "../../components/runs_select";
import {WidgetTitleEditor} from "../../components/widget_title_editor";

/**
 * @typedef {import('./state').CheckpointsWidgetState} CheckpointsWidgetState
 */

const validateOptions = (runIds, plotAllRuns) => {
  const errors = [];
  if (plotAllRuns === false && runIds.length === 0) {
    errors.push("At least one run must be selected.");
  }

  const isValid = errors.length === 0;

  return {isValid, errors};
};

const NullStateForNoCheckpoints = () => {
  return (
    <div>
      It looks like you have not reported any checkpoints.{" "}
      <a
        href={`${DOCS_URL}/ai-module-api-references/api_reference/python_tracking#sigopt.log_checkpoint-checkpoint_values`}
      >
        Visit the docs to learn how to record checkpoints.
      </a>
    </div>
  );
};

const AllRunsRadio = ({plotAllRuns, setPlotAllRuns}) => {
  return (
    <>
      <div className="form-check form-check-inline">
        <input
          className="form-check-input"
          type="radio"
          id="tableFilter"
          checked={plotAllRuns}
          onChange={setPlotAllRuns.bind(null, true)}
        />
        <label className="form-check-label" htmlFor="tableFilter">
          Use Main Table for Filtering Runs
        </label>
      </div>
      <div className="form-check form-check-inline">
        <input
          className="form-check-input"
          type="radio"
          id="specificRuns"
          checked={!plotAllRuns}
          onChange={setPlotAllRuns.bind(null, false)}
        />
        <label className="form-check-label" htmlFor="specificRuns">
          Select Specific Runs To Plot
        </label>
      </div>
    </>
  );
};

/**
 * @param {object} param
 * @param {CheckpointsWidgetState} param.initialWidgetData -
 * @param {function} param.setValid - is the current state valid (enabled create/save widget button)
 * @param {function} param.setWidgetData - sets current widgetData, only need to set if it is valid
 * @param {boolean} param.editing - if it is a widget being edited or a new widget
 * @param {any} param.runs - runs
 * @param {any} param.definedFields - definedFields
 */
export const UnconnectedCheckpointsWidgetEditor = ({
  initialWidgetData,
  setWidgetData,
  setValid,
  runs,
  definedFields,
}) => {
  const {state} = initialWidgetData;
  const [title, setTitle] = React.useState(initialWidgetData.title);
  const [plotAllRuns, setPlotAllRuns] = React.useState(state.plotAllRuns);
  const [runIds, setRunIds] = React.useState(state.runIds);

  React.useEffect(() => {
    const {isValid, errors} = validateOptions(runIds, plotAllRuns);
    setValid(isValid, errors);

    if (isValid) {
      const newWidgetData = CheckpointsWidgetStateBuilder(
        title,
        runIds,
        plotAllRuns,
      );
      setWidgetData(newWidgetData);
    }
  }, [title, runIds, plotAllRuns]);

  if (runs.length === 0) {
    return <NullStateForNoCheckpoints />;
  }

  return (
    <div className="flex-column full-width">
      <WidgetTitleEditor title={title} setTitle={setTitle} />

      <div className="flex-column" style={{marginTop: 15, marginLeft: 25}}>
        <AllRunsRadio
          plotAllRuns={plotAllRuns}
          setPlotAllRuns={setPlotAllRuns}
        />
      </div>

      {!plotAllRuns && (
        <div style={{height: 400, marginTop: 10}}>
          <RunsSelect
            selectedRunIds={runIds}
            setSelectedRunIds={setRunIds}
            runs={runs}
            definedFields={definedFields}
          />
        </div>
      )}
    </div>
  );
};

const mapStateToProps = (state) => ({
  runs: _.filter(state.dimensions.runs, (run) => run.checkpoint_count > 0),
  definedFields: state.dimensions.definedFields,
});

export const CheckpointsWidgetEditor = connect(mapStateToProps)(
  UnconnectedCheckpointsWidgetEditor,
);
