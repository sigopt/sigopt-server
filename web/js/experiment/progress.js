/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import pluralize from "pluralize";

import ui from "./ui";
import {CompactObservationsProgressBar} from "../pages/experiment/common/view/observation_progress_bar";
import {CompactRunsProgressBar} from "./runs_progress_bar";

const RawCount = ({object, count}) => pluralize(object, count, true);

export const CompactExperimentProgress = ({experiment}) => {
  if (ui.isAiExperiment(experiment)) {
    if (experiment.budget) {
      return <CompactRunsProgressBar experiment={experiment} />;
    }
    return (
      <RawCount object="Run" count={experiment.progress.finished_run_count} />
    );
  }
  if (experiment.observation_budget) {
    return <CompactObservationsProgressBar experiment={experiment} />;
  }
  return (
    <RawCount
      object="Observation"
      count={experiment.progress.observation_count}
    />
  );
};
