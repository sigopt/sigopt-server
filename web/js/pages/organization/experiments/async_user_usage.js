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

const query = (
  organizationId,
  promiseApiClient,
  userId,
  teamId,
  periodStart,
  periodEnd,
  limit = 0,
) => {
  let target = promiseApiClient.organizations(organizationId);
  if (teamId) {
    target = promiseApiClient.clients(teamId);
  }

  return target.experiments().fetch({
    development: false,
    limit: limit,
    period_start: periodStart,
    period_end: periodEnd,
    state: "all",
    user: userId,
    include_ai: true,
  });
};

const createUserUsageSourcePool = function (organizationId, promiseApiClient) {
  return new SourcePool((userId, teamId, periodStart, periodEnd, limit) =>
    query(
      organizationId,
      promiseApiClient,
      userId,
      teamId,
      periodStart,
      periodEnd,
      limit,
    ),
  );
};

const fetchUsersUsageData = (
  usersUsageDataPool,
  userIds,
  teamId,
  timePeriods,
) => {
  const userUsageMap = createUsageMap(timePeriods, userIds);

  const outstandingPromises = [];
  const usersLastExperimentP = eachWithDelay(
    userIds,
    (id) => {
      // Fetch users last experiment.
      outstandingPromises.push(
        usersUsageDataPool.get(id, teamId, null, null, 1).then((pagination) => {
          userUsageMap[id].lastExperiment = pagination.data[0];
        }),
      );
    },
    uniformRandomNumberGenerator(
      50 / MILLISECONDS_PER_SECOND,
      100 / MILLISECONDS_PER_SECOND,
    ),
  );

  const usersExperimentsByPeriodP = eachWithDelay(
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

  return Promise.all([usersLastExperimentP, usersExperimentsByPeriodP])
    .then(() => Promise.all(outstandingPromises))
    .then(() => userUsageMap);
};

export {createUserUsageSourcePool, fetchUsersUsageData};
