/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";

import schemas from "../react/schemas";
import ui from "../experiment/ui";

export const unifiedChartArgsProp = PropTypes.shape({
  bestAssignments: PropTypes.arrayOf(schemas.Observation.isRequired).isRequired,
  experiment: schemas.Experiment.isRequired,
  failures: PropTypes.arrayOf(schemas.Observation.isRequired).isRequired,
  metadataKeys: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
  observations: PropTypes.arrayOf(schemas.Observation.isRequired).isRequired,
  observationToRunMap: PropTypes.objectOf(PropTypes.string),
  successfulObservations: PropTypes.arrayOf(schemas.Observation.isRequired)
    .isRequired,
  successfulObservationsLessBestAssignments: PropTypes.arrayOf(
    schemas.Observation.isRequired,
  ).isRequired,
  successfulObservationsByTaskName: PropTypes.object.isRequired,
  successfulObservationsLessFullCost: PropTypes.arrayOf(schemas.Observation)
    .isRequired,
  fullCostTask: schemas.Task,
});

export const getUnifiedChartArgs = (
  experiment,
  observations,
  bestAssigns,
  runs,
) => {
  const [failures, notFailures] = _.partition(observations, (o) => o.failed);
  const [successfulObservations, unsuccessfulObservations] = _.partition(
    notFailures,
    (o) => ui.observationSatisfiesThresholds(experiment, o),
  );
  const bestAssignmentsSet = _.chain(bestAssigns)
    .map((ba) => [ba.id, true])
    .object()
    .value();
  const bestAssignments = _.filter(
    successfulObservations,
    (o) => bestAssignmentsSet[o.id],
  );
  const [
    notFailuresLessBestAssignments,
    successfulObservationsLessBestAssignments,
  ] = _.map([notFailures, successfulObservations], (obs) =>
    _.filter(obs, (o) => !bestAssignmentsSet[o.id]),
  );
  const metadataKeys = ui.getMetadataKeys(observations);

  const successfulObservationsByTaskName = experiment.tasks
    ? _.groupBy(successfulObservations, (o) => o.task.name)
    : {};

  const fullCostTask = experiment.tasks
    ? _.find(experiment.tasks, (t) => t.cost === 1)
    : null;
  const successfulObservationsLessFullCost = _.flatten(
    _.map(successfulObservationsByTaskName, (group, taskName) =>
      taskName === fullCostTask.name ? [] : group,
    ),
  );

  const observationToRunMap = _.chain(runs)
    .filter("observation")
    .map((run) => [run.observation, run.id])
    .object()
    .value();

  return {
    bestAssignments,
    experiment,
    failures,
    fullCostTask,
    metadataKeys,
    notFailures,
    notFailuresLessBestAssignments,
    observationToRunMap,
    observations,
    successfulObservations,
    successfulObservationsByTaskName,
    successfulObservationsLessBestAssignments,
    successfulObservationsLessFullCost,
    unsuccessfulObservations,
  };
};
