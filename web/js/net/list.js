/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/**
 * Takes in a array and emits a function that pages over that array, which
 * is suitable for consumption by functions such as `exhaustivelyPage`.
 */

import _ from "underscore";

import {coalesce} from "../utils";

export default function arrayPager(list) {
  return function (paging, success, error) {
    const pageSize = coalesce(paging.limit, _.size(list));

    if (!_.isArray(list) || !_.isNumber(pageSize) || pageSize < 0) {
      return error();
    }

    if (paging.after === undefined) {
      const before = paging.before || 0;
      const nextPage = before + pageSize;
      const newBefore = nextPage < list.length ? nextPage : null;
      return success({
        count: list.length,
        data: list.slice(before, coalesce(newBefore, list.length)),
        paging: {
          before: newBefore,
        },
      });
    } else {
      const after = coalesce(paging.after, list.length);
      const prevPage = after - pageSize;
      const newAfter = prevPage >= 0 ? prevPage : null;
      return success({
        count: list.length,
        data: list.slice(coalesce(newAfter, 0), after).reverse(),
        paging: {
          after: newAfter,
        },
      });
    }
  };
}
