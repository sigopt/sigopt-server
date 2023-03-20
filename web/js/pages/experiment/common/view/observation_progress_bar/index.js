/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import FlagCheckeredGlyph from "../../../../../component/glyph/flag-checkered";
import ProgressBar from "../../../../../component/progress_bar";
import {LongLabel, ShortLabel} from "./labels";

export const ObservationsProgressBar = function (props) {
  const budget = props.experiment.observation_budget;
  if (!budget) {
    return null;
  }
  const budgetConsumed = props.experiment.progress.observation_budget_consumed;
  const count = props.experiment.progress.observation_count;

  return (
    <div className="observation-budget-progress">
      <LongLabel
        budget={budget}
        budgetConsumed={budgetConsumed}
        count={count}
        experiment={props.experiment}
      />
      <ProgressBar width={_.min([budgetConsumed / budget, 1])} />
      {budgetConsumed < budget && <FlagCheckeredGlyph />}
    </div>
  );
};

export const CompactObservationsProgressBar = function (props) {
  const budget = props.experiment.observation_budget;
  if (!budget) {
    return null;
  }
  const budgetConsumed = props.experiment.progress.observation_budget_consumed;
  const count = props.experiment.progress.observation_count;

  return (
    <div className="observation-budget-progress">
      <ShortLabel
        budget={budget}
        budgetConsumed={budgetConsumed}
        count={count}
        experiment={props.experiment}
      />
      <ProgressBar width={_.min([budgetConsumed / budget, 1])} />
    </div>
  );
};
