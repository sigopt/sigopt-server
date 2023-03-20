/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {PagerMonitor, exhaustivelyPage} from "../../net/paging";

describe("exhaustivelyPage", () => {
  it("succeeds on empty arrays", (done) => {
    exhaustivelyPage(
      (paging, success) => success({data: [], paging: {before: null}}),
      {
        success: function (data) {
          expect(data).toEqual([]);
          done();
        },
        error: done.fail,
      },
    );
  });

  it("succeeds on full arrays", (done) => {
    exhaustivelyPage(
      (paging, success) => success({data: [1, 2, 3], paging: {before: null}}),
      {
        success: function (data) {
          expect(data).toEqual([1, 2, 3]);
          done();
        },
        error: done.fail,
      },
    );
  });

  it("handles error", (done) => {
    exhaustivelyPage(
      (paging, success, error) => error({message: "error message"}),
      {
        success: done.fail,
        error: function (response) {
          expect(response.message).toBe("error message");
          done();
        },
      },
    );
  });

  it("uses page size", (done) => {
    const fetcher = (paging, success) => {
      expect(paging.limit).toEqual(5);
      success({data: [1, 2], paging: {before: null}});
    };

    exhaustivelyPage(fetcher, {
      success: function (data) {
        expect(data).toEqual([1, 2]);
        done();
      },
      error: done.fail,
      limit: 5,
    });
  });

  describe("paging", () => {
    it("handles multiple pages", function (done) {
      let callCount = 0;
      const fetcher = (paging, success) => {
        callCount += 1;
        if (callCount === 1) {
          expect(paging.before).toBe(null);
          return success({
            data: [1, 2],
            paging: {before: 5, after: null},
          });
        } else if (callCount === 2) {
          expect(paging.before).toBe(5);
          return success({
            data: [3, 4],
            paging: {before: null, after: 4},
          });
        } else {
          return done.fail();
        }
      };
      exhaustivelyPage(fetcher, {
        success: (response) => {
          expect(response).toEqual([1, 2, 3, 4]);
          done();
        },
        error: done.fail,
      });
    });

    it("works with after", function (done) {
      let callCount = 0;
      const fetcher = (paging, success) => {
        callCount += 1;
        if (callCount === 1) {
          expect(paging.after).toBe(null);
          return success({
            data: [1, 2],
            paging: {after: 5, before: null},
          });
        } else if (callCount === 2) {
          expect(paging.after).toBe(5);
          return success({
            data: [3, 4],
            paging: {after: null, before: 4},
          });
        } else {
          return done.fail();
        }
      };
      exhaustivelyPage(fetcher, {
        success: (response) => {
          expect(response).toEqual([1, 2, 3, 4]);
          done();
        },
        error: done.fail,
        ascending: true,
      });
    });

    it("doesnt go the wrong way", function (done) {
      let callCount = 0;
      const fetcher = (paging, success) => {
        callCount += 1;
        if (callCount === 1) {
          return success({
            data: [1, 2],
            paging: {after: 5, before: null},
          });
        } else {
          return done.fail();
        }
      };
      exhaustivelyPage(fetcher, {
        success: (response) => {
          expect(response).toEqual([1, 2]);
          done();
        },
        error: done.fail,
        ascending: false,
      });
    });

    it("handles eventual errors", function (done) {
      let callCount = 0;
      const fetcher = (paging, success, error) => {
        callCount += 1;
        if (callCount === 1) {
          expect(paging.before).toBe(null);
          return success({
            data: [1, 2],
            paging: {before: 5, after: null},
          });
        } else if (callCount === 2) {
          return error();
        } else {
          return done.fail();
        }
      };
      exhaustivelyPage(fetcher, {success: done.fail, error: done});
    });
  });

  describe("cancel", () => {
    it("can be cancelled after completion", function (done) {
      const fetcher = jest.fn();
      const monitor = new PagerMonitor();
      exhaustivelyPage(fetcher, {error: done.fail, params: {monitor: monitor}});
      monitor.cancel();
      done();
    });

    it("can be cancelled multiple times", function (done) {
      const fetcher = jest.fn();
      const monitor = new PagerMonitor();
      exhaustivelyPage(fetcher, {error: done.fail, params: {monitor: monitor}});
      monitor.cancel();
      monitor.cancel();
      done();
    });

    it("would succeed without cancellation", function (done) {
      const fetcher = jest.fn();
      exhaustivelyPage(fetcher, {success: () => done(), error: done.fail});
      const ourSuccess = fetcher.mock.calls[0][1];
      ourSuccess({data: [], paging: {}});
    });

    it("prevents success on cancellation", function (done) {
      const fetcher = jest.fn();
      const monitor = new PagerMonitor();
      exhaustivelyPage(fetcher, {
        success: done.fail,
        error: done.fail,
        params: {monitor: monitor},
      });
      monitor.cancel();
      const ourSuccess = fetcher.mock.calls[0][1];
      ourSuccess({data: [], paging: {}});
      done();
    });

    it("would error without cancellation", function (done) {
      const fetcher = jest.fn();
      const err = new Error("Expected error");
      exhaustivelyPage(fetcher, {
        success: done.fail,
        error: (e) => {
          expect(err).toBe(e);
          done();
        },
      });
      const ourError = fetcher.mock.calls[0][2];
      ourError(err);
    });

    it("prevents error on cancellation", function (done) {
      const fetcher = jest.fn();
      const err = new Error("Should be ignored");
      const monitor = new PagerMonitor();
      exhaustivelyPage(fetcher, {
        success: done.fail,
        error: done.fail,
        params: {monitor: monitor},
      });
      monitor.cancel();
      const ourError = fetcher.mock.calls[0][2];
      ourError(err);
      done();
    });
  });
});
