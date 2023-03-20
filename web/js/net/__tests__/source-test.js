/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import AlertBroker from "../../alert/broker";
import ErrorNotifier from "../../alert/notify";
import {AsynchronousDataSource, AvailableDataSource} from "../source";

jest.mock("../../alert/notify");
jest.mock("../../alert/broker");

describe("DataSource", function () {
  const fetcher = jest.fn();
  const success = jest.fn();
  const error = jest.fn();
  const errorNotifier = new ErrorNotifier({alertBroker: new AlertBroker()});

  beforeEach(function () {
    fetcher.mockReset();
    success.mockReset();
    error.mockReset();
    errorNotifier.cleanupError.mockReset();
  });

  describe("AvailableDataSource", function () {
    it("always succeeds", function () {
      const source = new AvailableDataSource(1, 2, 3);
      source.getData(success, error);
      expect(success.mock.calls).toEqual([[1, 2, 3]]);
      expect(error.mock.calls).toEqual([]);
    });
  });

  describe("AsynchronousDataSource", function () {
    it("waits for results", function () {
      new AsynchronousDataSource(fetcher, errorNotifier);
      expect(fetcher.mock.calls).toEqual([]);
    });

    it("can succeed synchronously", function () {
      const ourFetcher = (s) => s(1, 2, 3);
      const source = new AsynchronousDataSource(ourFetcher, errorNotifier);
      source.getData(success, error);
      source.getData(success, error);
      expect(success.mock.calls).toEqual([
        [1, 2, 3],
        [1, 2, 3],
      ]);
      expect(error.mock.calls).toEqual([]);
    });

    it("can succeed asynchronously", function () {
      const source = new AsynchronousDataSource(fetcher, errorNotifier);
      source.getData(success, error);
      source.getData(success, error);
      expect(success.mock.calls).toEqual([]);
      expect(error.mock.calls).toEqual([]);

      // Trigger a success
      fetcher.mock.calls[0][0](1, 2, 3);

      expect(success.mock.calls).toEqual([
        [1, 2, 3],
        [1, 2, 3],
      ]);
      expect(error.mock.calls).toEqual([]);
    });

    it("can fail synchronously", function () {
      const ourFetcher = (s, e) => e(1, 2, 3);
      const source = new AsynchronousDataSource(ourFetcher, errorNotifier);
      source.getData(success, error);
      source.getData(success, error);
      expect(success.mock.calls).toEqual([]);
      expect(error.mock.calls).toEqual([
        [1, 2, 3],
        [1, 2, 3],
      ]);
    });

    it("can fail asynchronously", function () {
      const source = new AsynchronousDataSource(fetcher, errorNotifier);
      source.getData(success, error);
      source.getData(success, error);
      expect(success.mock.calls).toEqual([]);
      expect(error.mock.calls).toEqual([]);

      // Trigger an error
      fetcher.mock.calls[0][1](1, 2, 3);

      expect(success.mock.calls).toEqual([]);
      expect(error.mock.calls).toEqual([
        [1, 2, 3],
        [1, 2, 3],
      ]);
    });

    it("is idempotent", function () {
      const source = new AsynchronousDataSource(fetcher, errorNotifier);
      source.getData(success, error);
      source.getData(success, error);
      expect(fetcher.mock.calls).toHaveLength(1);
    });

    it("has a default error handler", function () {
      const netError = {message: "error message"};
      const ourFetcher = (s, e) => e(netError);
      const source = new AsynchronousDataSource(ourFetcher, errorNotifier);
      source.getData(success);
      expect(success.mock.calls).toHaveLength(0);
      expect(errorNotifier.cleanupError.mock.calls).toEqual([[netError]]);
    });
  });
});
