/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import ui from "../../experiment/ui";

export const RECENT_EXPERIMENT = "experiment";
export const RECENT_PROJECT = "project";
export const RECENT_RUN = "run";
const RECENT_ACTIVITY_PAGE_SIZE = 10;

const experimentToRecentActivity = (experiment) => {
  const experimentClassTitle =
    {
      aiexperiment: "AI Experiment",
      experiment: "Core Experiment",
    }[experiment.object] || "Experiment";
  return {
    classTitle: experimentClassTitle,
    extra: {
      experiment,
    },
    href: `/${experiment.object}/${experiment.id}`,
    inProject: ui.isAiExperiment(experiment) ? experiment.project : undefined,
    name: experiment.name,
    time: experiment.updated,
    type: RECENT_EXPERIMENT,
  };
};

const projectToRecentActivity = (project) => ({
  classTitle: "Project",
  extra: {
    projectId: project.id,
  },
  href: `/client/${project.client}/project/${project.id}`,
  name: project.name,
  time: project.created,
  type: RECENT_PROJECT,
});

const runToRecentActivity = (run) => ({
  classTitle: "Run",
  extra: {
    state: run.state,
  },
  href: `/run/${run.id}`,
  inProject: run.project,
  name: run.name,
  time: run.created,
  type: RECENT_RUN,
});

export default function getRecentActivity(promiseApiClient, clientId, userId) {
  const recentExperimentsP = promiseApiClient
    .clients(clientId)
    .experiments()
    .fetch({
      include_ai: false,
      limit: RECENT_ACTIVITY_PAGE_SIZE,
      user: userId,
      sort: "id",
    })
    .then(({data}) => data);
  const recentAiExperimentsP = promiseApiClient
    .clients(clientId)
    .aiexperiments()
    .fetch({
      limit: RECENT_ACTIVITY_PAGE_SIZE,
      user: userId,
      sort: "id",
    })
    .then(({data}) => data);
  const recentProjectsP = promiseApiClient
    .clients(clientId)
    .projects()
    .fetch({
      limit: RECENT_ACTIVITY_PAGE_SIZE,
      user: userId,
    })
    .then(({data}) => data);
  const recentRunsP = promiseApiClient
    .clients(clientId)
    .trainingRuns()
    .fetch({
      limit: RECENT_ACTIVITY_PAGE_SIZE,
      filters: JSON.stringify([
        {field: "user", operator: "==", value: userId},
        {field: "experiment", operator: "isnull"},
      ]),
    })
    .then(({data}) => data);
  return Promise.all([
    recentExperimentsP,
    recentAiExperimentsP,
    recentProjectsP,
    recentRunsP,
  ]).then(
    ([recentExperiments, recentAiExperiments, recentProjects, recentRuns]) => {
      return _.chain([
        _.map(recentRuns, runToRecentActivity),
        _.map(recentExperiments, experimentToRecentActivity),
        _.map(recentAiExperiments, experimentToRecentActivity),
        _.map(recentProjects, projectToRecentActivity),
      ])
        .flatten()
        .sortBy(({time}) => -time)
        .first(RECENT_ACTIVITY_PAGE_SIZE)
        .value();
    },
  );
}
