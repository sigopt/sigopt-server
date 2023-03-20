/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

export const CHECKPOINTS_WIDGET_TYPE = "CHECKPOINTS_WIDGET";

/**
 * @typedef CheckpointsWidgetStateState
 * @type {object}
 * @property {number[]} runIds - Id's of runs to plot
 * @property {boolean}  plotAllRuns - Plot all runs and use table for filtering
 */

// ********WARNING********
// ALL OF THIS IS GOING TO GO INTO THE DB
// You want to save things like the dimension keys not the actual dimensions themselves.
// You NEED everything here. ie version, type, layout, state
/**
 * @typedef CheckpointsWidgetState
 * @type {object}
 * @property {number} version - Used for migrations, start at 1.
 * @property {string} type    - The type of the widget, make sure this unique.
 * @property {object} layout  - Size for the widget see: https://github.com/STRML/react-grid-layout
 *                              Don't add x and y. Those will get added by the dashboard.
 * @property {string} title
 * @property {CheckpointsWidgetStateState} state - unique state for widget
 */

/**
 * @param {string} title

 * @returns {CheckpointsWidgetState}
 */
export const CheckpointsWidgetStateBuilder = (title, runIds, plotAllRuns) => ({
  version: 1,
  type: CHECKPOINTS_WIDGET_TYPE,
  layout: {w: 2, h: 7, minH: 4, minW: 1},
  state: {runIds, plotAllRuns},
  title,
});

export const CheckpointEditorStateBuilder = () => {
  const title = "All Runs";

  return CheckpointsWidgetStateBuilder(title, [], true);
};

const MAX_NUM_RUNS = 5;
export const CheckpointDefaultStateBuilder = (runs) => {
  const runsWithCheckpoints = _.filter(runs, (run) => run.checkpoint_count > 0);
  if (runsWithCheckpoints.length === 0) {
    return false;
  }

  const runsSortedByUpdated = _.sortBy(runsWithCheckpoints, (run) =>
    Number(run.updated),
  );
  const runsIds = _.pluck(runsSortedByUpdated.slice(0, MAX_NUM_RUNS), "id");

  const numRuns = runsIds.length;
  const title = `Checkpoints - ${numRuns} Most Recently Updated Runs`;

  return CheckpointsWidgetStateBuilder(title, runsIds, false);
};
