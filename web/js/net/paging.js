/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

/**
 * Pages through API requests until there are not more pages to fetch, then call success on all of the data.
 * Otherwise call error.
 *
 * fetcher is a function that takes 3 parameters.
 *   The first is a paging block, which can be of the form {limit: X, before: Y, after: Z}.
 *   The second is success, the third is error.
 */
import {isDefinedAndNotNull} from "../utils";

export class PagerMonitor {
  constructor() {
    this.cancelled = false;
  }

  cancel() {
    this.cancelled = true;
  }
}

export const exhaustivelyPage = (fetcher, options) => {
  const o = _.extend(
    {
      success: () => undefined,
      error: () => undefined,
      limit: 1000,
      params: {},
      ascending: false,
    },
    options,
  );
  _.extend(o.params, {limit: o.limit});
  _.extend(o.params, {ascending: o.ascending});
  const direction = o.ascending ? "after" : "before";
  const getMarker = (paging) => paging[direction];

  const monitor = (o.params && o.params.monitor) || null;
  const fetchNextPage = (soFar, marker) => {
    fetcher(
      _.extend({[direction]: marker}, o.params),
      (response) => {
        const data = soFar.concat(response.data);
        const nextMarker = getMarker(response.paging);
        if (monitor && monitor.cancelled) {
          return;
        } else if (isDefinedAndNotNull(nextMarker)) {
          fetchNextPage(data, nextMarker);
        } else {
          o.success(data);
          return;
        }
      },
      (...args) => {
        if (monitor && monitor.cancelled) {
          return;
        } else {
          o.error(...args);
          return;
        }
      },
    );
  };

  fetchNextPage([], null);
};
