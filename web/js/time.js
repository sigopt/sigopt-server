/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import dateFnsAddMonths from "date-fns/add_months";
import dateFnsSubMonths from "date-fns/sub_months";
import dateFormat from "date-fns/format";
import differenceInMonths from "date-fns/difference_in_months";

export const subtractMonthsUnix = (seconds, months) =>
  dateFnsSubMonths(new Date(seconds * 1000), months).getTime() / 1000;
export const addMonthsUnix = (seconds, months) =>
  dateFnsAddMonths(new Date(seconds * 1000), months).getTime() / 1000;
export const subtractOneMonthUnix = (seconds) => subtractMonthsUnix(seconds, 1);
export const howManyMonthsFromNow = (seconds) =>
  differenceInMonths(new Date(seconds * 1000), new Date());

export const getTimePeriodLabel = () => {
  const now = new Date();
  return dateFormat(new Date(now.getYear(), now.getMonth(), 1), "MMMM");
};

const createTimePeriodLabels = function (timePeriod) {
  const DATE_FORMAT = "MMM";
  const startDateString = dateFormat(
    new Date(timePeriod.start * 1000),
    DATE_FORMAT,
  );
  const endDateString = dateFormat(
    new Date(timePeriod.end * 1000),
    DATE_FORMAT,
  );
  const startEndLabel = `${startDateString} - ${endDateString}`;
  const label = DATE_FORMAT === "MMM" ? endDateString : startEndLabel;

  return {
    DATE_FORMAT,
    startDateString,
    endDateString,
    startEndLabel,
    label,
  };
};

export const getCurrentPeriodEnd = function () {
  const now = new Date();
  const startOfNextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  return Math.floor(startOfNextMonth / 1000);
};

export const calculateLastNPeriods = function (numPeriods, currentPeriodEnd) {
  const startDate = subtractMonthsUnix(currentPeriodEnd, numPeriods);

  const periods = _.map(_.range(numPeriods), (i) => ({
    index: i,
    start: addMonthsUnix(startDate, i),
    end: addMonthsUnix(startDate, i + 1),
  }));

  return _.map(periods, (period) =>
    _.extend(period, createTimePeriodLabels(period)),
  );
};
