/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {compactDuration, fromNow, lookPretty} from "../nice-times.js";

const createCase = function (value, expected) {
  return {
    input: value,
    expected: expected,
  };
};

const negativeSeconds = createCase(-1, null);
const zeroSeconds = createCase(0, "less than one second");
const lessThanOneSecond = createCase(0.5, "less than one second");
const oneSecond = createCase(1, "1 second");
const oneSecondToOneMinute = createCase(30, "30 seconds");
const oneMinute = createCase(1 * 60, "1 minute");
const oneMinuteToOneHour = createCase(30 * 60, "30 minutes");
const oneHour = createCase(60 * 60, "1 hour");
const oneHourToOneDay = createCase(12 * 60 * 60, "12 hours");
const oneDay = createCase(24 * 60 * 60, "1 day");
const moreThanOneDay = createCase(10 * 24 * 60 * 60, "10 days");

const positiveCases = [
  lessThanOneSecond,
  oneSecond,
  oneSecondToOneMinute,
  oneMinute,
  oneMinuteToOneHour,
  oneHour,
  oneHourToOneDay,
  oneDay,
  moreThanOneDay,
];

const nonNegativeCases = [zeroSeconds].concat(positiveCases);

const allCases = [negativeSeconds].concat(nonNegativeCases);

// fixed date for testing
const now = new Date(1500931320000);

const fromNowTestFunction = (input) =>
  fromNow(now.getTime() / 1000 + input, now.getTime() / 1000);

describe("nice-times", function () {
  it("makes the time difference look nice (lookPretty)", () => {
    _.each(allCases, ({input, expected}) =>
      expect(lookPretty(input)).toEqual(expected),
    );
  });

  it("makes the time difference from now look nice (fromNow)", function () {
    expect(fromNowTestFunction(zeroSeconds.input)).toEqual(
      `${zeroSeconds.expected} ago`,
    );
    _.each(positiveCases, function ({input, expected}) {
      expect(fromNowTestFunction(input)).toEqual(`in ${expected}`);
      expect(fromNowTestFunction(-input)).toEqual(`${expected} ago`);
    });
  });

  it("renders durations in a compact format (compactDuration)", function () {
    _.each(
      [
        [0, "0s"],
        [30, "30s"],
        [60, "1m, 0s"],
        [60 + 30, "1m, 30s"],
        [30 * 60 + 30, "30m, 30s"],
        [60 * 60, "1h, 0m"],
        [60 * 60 + 30 * 60, "1h, 30m"],
        [60 * 60 + 30 * 60 + 30, "1h, 30m"],
        [12 * 60 * 60 + 30 * 60, "12h, 30m"],
        [24 * 60 * 60, "1d, 0h"],
        [24 * 60 * 60 + 30, "1d, 0h"],
        [24 * 60 * 60 + 12 * 60 * 60, "1d, 12h"],
        [99 * 24 * 60 * 60 + 12 * 60 * 60, "99d, 12h"],
      ],
      function ([input, expected]) {
        expect(compactDuration(input)).toEqual(expected);
      },
    );
  });
});
