/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import PromiseApiClient from "../promise-api-client";

describe("PromiseApiClient", () => {
  const requestor = jest.fn();
  const client = new PromiseApiClient(
    {
      apiRequestor: {
        request: requestor,
      },
    },
    {
      apiToken: "API_TOKEN",
      apiUrl: "https://sigopt.ninja:4443/api",
    },
  );
  const params = {a: "abc"};

  beforeEach(() => {
    requestor.mockReset();
  });

  describe("call format", () => {
    const checkCall = (
      call,
      method,
      path,
      checkParams,
      done,
      pathPrefix = "/v1",
    ) => {
      call.then(done).catch(done.fail);
      expect(requestor.mock.calls[0][0]).toEqual(method);
      expect(requestor.mock.calls[0][1]).toEqual(path);
      expect(requestor.mock.calls[0][2]).toEqual(checkParams);
      expect(requestor.mock.calls[0][5]).toEqual(false); // useLegacyErrorNotifier should always be false for promise
      expect(requestor.mock.calls[0][6]).toEqual(pathPrefix);
      requestor.mock.calls[0][3]();
    };

    it("GET /clients/X", (done) => {
      checkCall(
        client.clients(1).fetch(params),
        "GET",
        "/clients/1",
        params,
        done,
      );
    });

    it("POST /clients/X/experiments", (done) => {
      checkCall(
        client.clients(1).experiments().create(params),
        "POST",
        "/clients/1/experiments",
        params,
        done,
      );
    });

    it("PUT /experiments/X/observations/Y", (done) => {
      checkCall(
        client.experiments(1).observations(2).update(params),
        "PUT",
        "/experiments/1/observations/2",
        params,
        done,
      );
    });

    it("DELETE /experiments", (done) => {
      checkCall(
        client.experiments().delete(params),
        "DELETE",
        "/experiments",
        params,
        done,
      );
    });
  });

  describe("exhaustive paging", () => {
    it("pages", (done) => {
      requestor.mockImplementationOnce((a, b, c, success) =>
        success({
          data: ["1", "2", "3"],
          paging: {before: "ghi"},
        }),
      );
      requestor.mockImplementationOnce((a, b, c, success) =>
        success({
          data: ["4", "5", "6"],
          paging: {before: null},
        }),
      );

      const manuallyIncludedParams = {abc: "def"};
      const defaultParams = {ascending: false, limit: 1000};
      const compareParams = _.extend({}, manuallyIncludedParams, defaultParams);
      client
        .experiments()
        .exhaustivelyPage(manuallyIncludedParams)
        .then((results) => {
          expect(results).toEqual(["1", "2", "3", "4", "5", "6"]);
          expect(requestor.mock.calls).toHaveLength(2);
          expect(requestor.mock.calls[0].slice(0, 3)).toEqual([
            "GET",
            "/experiments",
            _.extend({before: null}, compareParams),
          ]);
          expect(requestor.mock.calls[1].slice(0, 3)).toEqual([
            "GET",
            "/experiments",
            _.extend({before: "ghi"}, compareParams),
          ]);
          done();
        })
        .catch(done.fail);
    });
  });
});
