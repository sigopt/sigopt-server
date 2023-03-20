/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import makeBestSeenTrace from "../best_seen_trace";

describe("makeBestSeenTrace", () => {
  _.each(
    [
      {
        aggregate: "min",
        expected: [
          {point: 1, value: 1},
          {point: 0, value: 0},
          {point: 0, value: 0},
          {point: -1, value: -1},
          {point: -1, value: -1},
        ],
      },
      {
        aggregate: "max",
        expected: [
          {point: 1, value: 1},
          {point: 1, value: 1},
          {point: 2, value: 2},
          {point: 2, value: 2},
          {point: 3, value: 3},
        ],
      },
    ],
    ({aggregate, expected}) => {
      const data = [1, 0, 2, -1, 3];
      it(`computes the ${aggregate} trace`, () => {
        const reject = _.noop;
        const getValue = _.identity;
        const trace = makeBestSeenTrace(data, {
          reject,
          getValue,
          aggregate: _[aggregate],
        });
        expect(trace).toEqual(expected);
      });
    },
  );

  it("rejects appropriate values", () => {
    const data = [
      {reject: true},
      {inputValue: 0, reject: true},
      {inputValue: 0, inputData: "test"},
      {inputValue: 1, reject: true},
      {inputValue: 1},
    ];
    const reject = _.property("reject");
    const getValue = _.property("inputValue");
    const trace = makeBestSeenTrace(data, {reject, getValue, aggregate: _.max});
    expect(trace).toEqual([
      null,
      null,
      {point: {inputValue: 0, inputData: "test"}, value: 0},
      {point: {inputValue: 0, inputData: "test"}, value: 0},
      {point: {inputValue: 1}, value: 1},
    ]);
  });
});
