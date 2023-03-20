/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import cartesian from "cartesian";

import SourcePool from "../../../net/pool";
import {MILLISECONDS_PER_SECOND} from "../../../constants";
import {createUsageMap} from "./lib";
import {eachWithDelay, uniformRandomNumberGenerator} from "../../../utils";

const query = (promiseApiClient, teamId, periodStart, periodEnd) =>
  promiseApiClient.clients(teamId).experiments().fetch({
    development: false,
    limit: 0,
    period_start: periodStart,
    period_end: periodEnd,
    state: "all",
    include_ai: true,
  });

const createTeamUsageSourcePool = (promiseApiClient) =>
  new SourcePool((teamId, periodStart, periodEnd) =>
    query(promiseApiClient, teamId, periodStart, periodEnd),
  );

const fetchTeamsUsageData = (teamsUsageDataPool, teamIds, timePeriods) => {
  const teamsUsageMap = createUsageMap(timePeriods, teamIds);

  const outstandingPromises = [];
  const teamsExperimentsByPeriodP = eachWithDelay(
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

  return Promise.all([teamsExperimentsByPeriodP])
    .then(() => Promise.all(outstandingPromises))
    .then(() => teamsUsageMap);
};

export {createTeamUsageSourcePool, fetchTeamsUsageData};
