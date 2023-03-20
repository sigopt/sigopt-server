/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

export const createUsageMap = function (timePeriods, ids) {
  const usageMap = {};
  _.forEach(ids, (id) => {
    const timePeriodsClone = _.map(timePeriods, (t) => _.clone(t));
    const timePeriodsByLabel = _.indexBy(timePeriodsClone, "label");
    usageMap[id] = {timePeriods: timePeriodsByLabel};
  });

  return usageMap;
};
