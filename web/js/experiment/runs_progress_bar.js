/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./runs_progress_bar.less";

import _ from "underscore";
import React from "react";
import pluralize from "pluralize";

import AngleRightGlyph from "../component/glyph/angle-right";
import FlagCheckeredGlyph from "../component/glyph/flag-checkered";
import ProgressBar from "../component/progress_bar";
import TriangleExclamationGlyph from "../component/glyph/triangle-exclamation";
import ui from "../experiment/ui";

const LongLabel = function (props) {
  return (
    <div className="runs-progress-title-label">
      {`${props.budgetConsumed}/${props.budget} Runs`}
    </div>
  );
};

const ShortLabel = function (props) {
  return (
    <div className="runs-progress-compact-title-label">{`${props.budgetConsumed}/${props.budget}`}</div>
  );
};

export const RunsProgressBar = function (props) {
  const budget = props.experiment.budget;
  if (!budget) {
    return null;
  }
  const budgetConsumed = props.experiment.progress.finished_run_count;

  return (
    <div className="runs-budget-progress full">
      <LongLabel budget={budget} budgetConsumed={budgetConsumed} />
      <ProgressBar width={_.min([budgetConsumed / budget, 1])} />
      {budgetConsumed < budget && (
        <FlagCheckeredGlyph className="budget-status-glyph" />
      )}
    </div>
  );
};

const FailedCountLink = (props) => {
  let message = "No Failures ";
  if (props.failedRuns > 0) {
    message = (
      <>
        <TriangleExclamationGlyph className="exclamation-color" />{" "}
        {`${props.failedRuns} ${pluralize("Failure", props.failedRuns)}`}
      </>
    );
  }
  return (
    <a
      href={ui.getExperimentUrl(props.experiment, "/history")}
      className="experiment-progress-row failures"
    >
      <div className="experiment-progress-text">{message}</div>{" "}
      <div className="glyph-angle">
        <AngleRightGlyph className="glyph-angle" />
      </div>
    </a>
  );
};

export const ExperimentBudgetProgressBar = function (props) {
  const budget = props.experiment.budget;
  const budgetConsumed = props.experiment.progress.finished_run_count;
  const experimentStatusString =
    budgetConsumed < budget ? "Experiment In Progress" : "Experiment Completed";
  if (budget) {
    return (
      <div className="experiment-progress">
        <div className="experiment-progress-row">
          <div className="experiment-text">{experimentStatusString}</div>
          <FailedCountLink {...props} />
        </div>
        <div className="experiment-progress-row">
          <div className="runs-budget-progress experiment">
            <ProgressBar width={_.min([budgetConsumed / budget, 1])} />
          </div>
        </div>
        <div className="experiment-progress-footer">
          <div className="experiment-text">
            {`${budgetConsumed}/${budget}`} Runs
          </div>
        </div>
      </div>
    );
  } else if (budgetConsumed) {
    return (
      <div className="experiment-progress no-budget">
        <div className="experiment-progress-row-no-budget">
          <div className="no-budget-runs">
            <div className="experiment-text">{budgetConsumed} Runs</div>
          </div>
          <div>
            <FailedCountLink {...props} />
          </div>
        </div>
      </div>
    );
  } else {
    return null;
  }
};

export const CompactRunsProgressBar = function (props) {
  const budget = props.experiment.budget;
  if (!budget) {
    return null;
  }
  const budgetConsumed = props.experiment.progress.finished_run_count;

  return (
    <div className="runs-budget-progress compact">
      <ShortLabel budget={budget} budgetConsumed={budgetConsumed} />
      <ProgressBar width={_.min([budgetConsumed / budget, 1])} />
    </div>
  );
};
