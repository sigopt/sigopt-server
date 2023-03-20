/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import cartesian from "cartesian";

import SourcePool from "../../../net/pool";
import {MILLISECONDS_PER_SECOND} from "../../../constants";
import {createTrainingRunFilters, createUsageMap} from "./lib";
import {eachWithDelay, uniformRandomNumberGenerator} from "../../../utils";

const query = (
  promiseApiClient,
  teamId,
  periodStart,
  periodEnd,
  optimized,
  limit = 0,
) => {
  const filterArray = createTrainingRunFilters(
    null,
    periodStart,
    periodEnd,
    optimized,
  );

  return promiseApiClient
    .clients(teamId)
    .trainingRuns()
    .fetch({
      filters: JSON.stringify(filterArray),
      limit: limit,
    });
};

const createTeamRunsUsageSourcePool = (promiseApiClient, optimized) =>
  new SourcePool((teamId, periodStart, periodEnd, limit) =>
    query(promiseApiClient, teamId, periodStart, periodEnd, optimized, limit),
  );

const fetchTeamsRunsUsageData = (teamsUsageDataPool, teamIds, timePeriods) => {
  const teamsUsageMap = createUsageMap(timePeriods, teamIds);

  const outstandingPromises = [];
  const teamsRunsByPeriodP = eachWithDelay(
    cartesian({teamId: teamIds, timePeriod: timePeriods}),
    ({teamId, timePeriod}) => {
      outstandingPromises.push(
        teamsUsageDataPool
          .get(teamId, timePeriod.start, timePeriod.end)
          .then((pagination) => {
            teamsUsageMap[teamId].timePeriods[timePeriod.label].count =
              pagination.count;
          }),
      );
    },
    uniformRandomNumberGenerator(
      50 / MILLISECONDS_PER_SECOND,
      150 / MILLISECONDS_PER_SECOND,
    ),
  );

  return Promise.all([teamsRunsByPeriodP])
    .then(() => Promise.all(outstandingPromises))
    .then(() => teamsUsageMap);
};

export {createTeamRunsUsageSourcePool, fetchTeamsRunsUsageData};
