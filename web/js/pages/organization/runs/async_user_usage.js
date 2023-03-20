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
  organizationId,
  promiseApiClient,
  userId,
  teamId,
  periodStart,
  periodEnd,
  optimized,
  limit = 0,
) => {
  let target = promiseApiClient.organizations(organizationId);
  if (teamId) {
    target = promiseApiClient.clients(teamId);
  }

  const filterArray = createTrainingRunFilters(
    userId,
    periodStart,
    periodEnd,
    optimized,
  );

  return target.trainingRuns().fetch({
    filters: JSON.stringify(filterArray),
    limit: limit,
  });
};

const createUserRunsUsageSourcePool = function (
  organizationId,
  promiseApiClient,
  optimized,
) {
  return new SourcePool((userId, teamId, periodStart, periodEnd, limit) =>
    query(
      organizationId,
      promiseApiClient,
      userId,
      teamId,
      periodStart,
      periodEnd,
      optimized,
      limit,
    ),
  );
};

const fetchUsersRunsUsageData = (
  usersUsageDataPool,
  userIds,
  teamId,
  timePeriods,
) => {
  const userUsageMap = createUsageMap(timePeriods, userIds);

  const outstandingPromises = [];
  const usersLastRunsP = eachWithDelay(
    userIds,
    (id) => {
      // Fetch users last runs.
      outstandingPromises.push(
        usersUsageDataPool.get(id, teamId, null, null, 1).then((pagination) => {
          userUsageMap[id].lastRun = pagination.data[0];
        }),
      );
    },
    uniformRandomNumberGenerator(
      50 / MILLISECONDS_PER_SECOND,
      100 / MILLISECONDS_PER_SECOND,
    ),
  );

  const usersRunsByPeriodP = eachWithDelay(
    cartesian({id: userIds, timePeriod: timePeriods}),
    ({id, timePeriod}) => {
      // Fetch experiment counts for each time period.
      outstandingPromises.push(
        usersUsageDataPool
          .get(id, teamId, timePeriod.start, timePeriod.end)
          .then((pagination) => {
            userUsageMap[id].timePeriods[timePeriod.label].count =
              pagination.count;
          }),
      );
    },
    uniformRandomNumberGenerator(
      50 / MILLISECONDS_PER_SECOND,
      100 / MILLISECONDS_PER_SECOND,
    ),
  );

  return Promise.all([usersLastRunsP, usersRunsByPeriodP])
    .then(() => Promise.all(outstandingPromises))
    .then(() => userUsageMap);
};

export {createUserRunsUsageSourcePool, fetchUsersRunsUsageData};
