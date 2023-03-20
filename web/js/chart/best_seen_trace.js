/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {metricValueGetter} from "./values";

export default function makeBestSeenTrace(
  data,
  {
    aggregate = _.max,
    getValue = (o) => metricValueGetter(o, 0),
    reject = _.property("failed"),
  } = {},
) {
  /*
   * generalizable algorithm to compute the best seen trace
   *
   * data: array
   *  input data for computing the trace
   *
   * aggregate: function
   *  determines which point is best from a filtered list of points
   *  should be _.min or _.max
   *
   * getValue: function
   *  returns the numerical value of the data point
   *
   * reject: function
   *  used to reject data from consideration for the best trace
   *
   * return: array of objects or null
   *  represents the computed best seen trace
   *  objects have the following structure
   *
   *  point: any
   *    item from the input array that represents the best value so far
   *
   *  value: number
   *    represents the best value so far
   *    retrieved by applying getValue on the point
   *
   */

  return _.chain(data)
    .map((d) => (reject(d) ? null : {point: d, value: getValue(d)}))
    .reduce((bestTrace, next) => {
      const lastBest = _.last(bestTrace);
      const considerablePoints = [lastBest, next];
      const acceptablePoints = _.filter(considerablePoints);
      const nextBest = _.isEmpty(acceptablePoints)
        ? null
        : aggregate(acceptablePoints, "value");
      bestTrace.push(nextBest);
      return bestTrace;
    }, [])
    .value();
}
