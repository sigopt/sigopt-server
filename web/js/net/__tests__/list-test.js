/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import arrayPager from "../../net/list";
import {exhaustivelyPage} from "../../net/paging";

describe("arrayPager", () => {
  const expectedResults = function (
    expectedCount,
    expectedData,
    expectedBefore,
    expectedAfter,
  ) {
    return function (response) {
      expect(response.count).toBe(expectedCount);
      expect(response.data).toEqual(expectedData);
      expect(response.paging.before).toBe(expectedBefore);
      expect(response.paging.after).toBe(expectedAfter);
    };
  };

  it("handles empty arrays", () => {
    const pager = arrayPager([]);
    pager({limit: 0}, expectedResults(0, [], null, undefined));
    pager({limit: 5}, expectedResults(0, [], null, undefined));
    pager({before: 1, limit: 10}, expectedResults(0, [], null, undefined));
    pager({before: 10, limit: 100}, expectedResults(0, [], null, undefined));
    pager({after: 1, limit: 10}, expectedResults(0, [], undefined, null));
    pager({after: 10, limit: 100}, expectedResults(0, [], undefined, null));
  });

  it("handles normal arrays", () => {
    const pager = arrayPager([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]);

    pager({limit: 0}, expectedResults(11, [], 0, undefined));
    pager({before: 0, limit: 0}, expectedResults(11, [], 0, undefined));
    pager({before: 3, limit: 0}, expectedResults(11, [], 3, undefined));
    pager({limit: 5}, expectedResults(11, [1, 2, 3, 4, 5], 5, undefined));
    pager(
      {before: 0, limit: 5},
      expectedResults(11, [1, 2, 3, 4, 5], 5, undefined),
    );
    pager(
      {before: 3, limit: 5},
      expectedResults(11, [4, 5, 6, 7, 8], 8, undefined),
    );
    pager({before: 10, limit: 5}, expectedResults(11, [11], null, undefined));
    pager({before: 100, limit: 5}, expectedResults(11, [], null, undefined));
    pager(
      {after: null, limit: 5},
      expectedResults(11, [11, 10, 9, 8, 7], undefined, 6),
    );
    pager(
      {after: 11, limit: 5},
      expectedResults(11, [11, 10, 9, 8, 7], undefined, 6),
    );
    pager({after: 1, limit: 5}, expectedResults(11, [1], undefined, null));
    pager({after: 0, limit: 5}, expectedResults(11, [], undefined, null));
  });

  it("works with exhaustivelyPage", () => {
    _.each(
      [
        [[], 1],
        [[], 5],
        [[1, 2, 3], 1],
        [[1, 2, 3], 5],
        [[1, 2, 3, 4, 5], 2],
      ],
      ([array, pageSize]) => {
        const pager = arrayPager(array, pageSize);
        const success = jest.fn();
        exhaustivelyPage(pager, {success: success, limit: pageSize});
        expect(success.mock.calls).toEqual([[array]]);
      },
    );
  });
});
