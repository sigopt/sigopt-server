/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import ProjectEndpoint from "../server/endpoint";

const recentActivityMax = 10;

export default class ProjectOverviewEndpoint extends ProjectEndpoint {
  pageName() {
    return "Overview";
  }

  static page = require("./page");

  parseParams(req) {
    const allMetricsP = this._getAllMetrics(req);
    const recentActionsP = this._getRecentActions(req);
    return Promise.all([allMetricsP, recentActionsP]).then(
      ([metrics, recentActions]) => ({
        metrics,
        recentActions,
      }),
    );
  }

  _getAllMetrics(req) {
    const runsP = req.services.promiseApiClient
      .clients(req.matchedProject.client)
      .projects(req.matchedProject.id)
      .trainingRuns()
      .fetch({limit: 0});
    return runsP.then(({defined_fields}) =>
      _.chain(defined_fields)
        .pluck("key")
        .filter((key) => key.startsWith("values.") && key.endsWith(".value"))
        .map((key) =>
          key.substr("values.".length, key.length - "values..value".length),
        )
        .sort()
        .value(),
    );
  }

  _getRecentActions(req) {
    const recentExperimentsP = req.services.promiseApiClient
      .clients(req.matchedProject.client)
      .projects(req.matchedProject.id)
      .experiments()
      .fetch({limit: recentActivityMax, sort: "recent"})
      .then(({data}) => data);
    const thisProjectCreatedActivitiesP = Promise.resolve([
      {
        by: req.matchedProject.user,
        for: "project",
        key: `project:${req.matchedProject.id}`,
        object: req.matchedProject,
        time: req.matchedProject.created,
        type: "create",
      },
    ]);
    const experimentCreatedActivitiesP = recentExperimentsP.then(
      (experiments) =>
        _.map(experiments, (exp) => ({
          by: exp.user,
          for: "experiment",
          key: `experiment:${exp.id}`,
          object: exp,
          time: exp.created,
          type: "create",
        })),
    );
    const experimentUpdatedActivitiesP = recentExperimentsP.then(
      (experiments) =>
        _.map(experiments, (exp) => ({
          by: exp.user,
          duration: {start: exp.created, end: exp.updated},
          for: "experiment",
          key: `experiment:${exp.id}`,
          object: exp,
          time: exp.updated,
          type: "update",
        })),
    );
    const runFilters = JSON.stringify([
      {
        field: "experiment",
        operator: "isnull",
      },
    ]);
    const runCreatedActivitiesP = req.services.promiseApiClient
      .clients(req.matchedProject.client)
      .projects(req.matchedProject.id)
      .trainingRuns()
      .fetch({
        sort: "created",
        limit: recentActivityMax,
        filters: runFilters,
      })
      .then(({data}) =>
        _.map(data, (run) => ({
          by: run.user,
          for: "run",
          key: `run:${run.id}`,
          object: run,
          time: run.created,
          type: "create",
        })),
      );
    const runUpdatedActivitiesP = req.services.promiseApiClient
      .clients(req.matchedProject.client)
      .projects(req.matchedProject.id)
      .trainingRuns()
      .fetch({
        sort: "updated",
        limit: recentActivityMax,
        filters: runFilters,
      })
      .then(({data}) =>
        _.chain(data)
          .filter((run) => run.state === "active")
          .map((run) => ({
            by: run.user,
            duration: {start: run.created, end: run.updated},
            for: "run",
            key: `run:${run.id}`,
            object: run,
            time: run.updated,
            type: "update",
          }))
          .value(),
      );
    const runCompletedActivitiesP = req.services.promiseApiClient
      .clients(req.matchedProject.client)
      .projects(req.matchedProject.id)
      .trainingRuns()
      .fetch({
        sort: "completed",
        limit: recentActivityMax,
        filters: runFilters,
      })
      .then(({data}) =>
        _.map(data, (run) => {
          const type = run.state === "failed" ? "fail" : "complete";
          return {
            by: run.user,
            duration: {start: run.created, end: run.completed},
            for: "run",
            key: `run:${run.id}`,
            object: run,
            time: run.completed,
            type,
          };
        }),
      );
    return Promise.all([
      runCompletedActivitiesP,
      runUpdatedActivitiesP,
      runCreatedActivitiesP,
      experimentUpdatedActivitiesP,
      experimentCreatedActivitiesP,
      thisProjectCreatedActivitiesP,
    ]).then((allActivities) =>
      _.chain(allActivities)
        .flatten()
        .reverse()
        .indexBy("key")
        .values()
        .sortBy(({time}) => -time)
        .first(recentActivityMax)
        .value(),
    );
  }
}
