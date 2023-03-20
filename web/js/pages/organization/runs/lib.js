/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {isDefinedAndNotNull} from "../../../utils";

export const createUsageMap = function (timePeriods, ids) {
  const usageMap = {};
  _.forEach(ids, (id) => {
    const timePeriodsClone = _.map(timePeriods, (t) => _.clone(t));
    const timePeriodsByLabel = _.indexBy(timePeriodsClone, "label");
    usageMap[id] = {timePeriods: timePeriodsByLabel};
  });

  return usageMap;
};

export const createTrainingRunFilters = function (
  userId,
  periodStart,
  periodEnd,
  optimized,
) {
  // eslint and prettier disagree on how this code should look, so we disable the eslint rule for this and let prettier win, since
  // it rewrites on every commit.
  const arrayOfFilters = [];
  if (isDefinedAndNotNull(optimized))
    // eslint-disable-next-line nonblock-statement-body-position
    arrayOfFilters.push({
      field: "optimized_suggestion",
      operator: "==",
      value: optimized,
    });
  if (isDefinedAndNotNull(periodEnd))
    // eslint-disable-next-line nonblock-statement-body-position
    arrayOfFilters.push({field: "created", operator: "<", value: periodEnd});
  if (isDefinedAndNotNull(periodStart))
    // eslint-disable-next-line nonblock-statement-body-position
    arrayOfFilters.push({field: "created", operator: ">=", value: periodStart});
  if (isDefinedAndNotNull(userId))
    // eslint-disable-next-line nonblock-statement-body-position
    arrayOfFilters.push({field: "user", operator: "==", value: userId});
  return arrayOfFilters;
};
