/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LegacyApiClient from "../legacy-api-client";

describe("LegacyApiClient", () => {
  const requestor = jest.fn();
  const client = new LegacyApiClient(
    {
      alertBroker: {
        clearAlerts: jest.fn(),
      },
      apiRequestor: {
        request: requestor,
      },
    },
    {
      apiToken: "API_TOKEN",
      apiUrl: "https://sigopt.ninja:4443/api",
    },
  );
  const success = jest.fn();
  const error = jest.fn();
  const params = {a: "abc"};

  describe("call format", () => {
    beforeEach(() => {
      requestor.mockReset();
      success.mockReset();
      error.mockReset();
    });

    it("supports (id, success, error)", () => {
      client.experimentCreate("1", success, error);
      expect(requestor.mock.calls[0]).toEqual([
        "POST",
        "/clients/1/experiments",
        {},
        success,
        error,
        true,
      ]);
    });

    it("supports (id, success)", () => {
      client.experimentCreate("1", success);
      expect(requestor.mock.calls[0]).toEqual([
        "POST",
        "/clients/1/experiments",
        {},
        success,
        null,
        true,
      ]);
    });

    it("supports (id, params, success, error)", () => {
      client.experimentCreate("1", params, success, error);
      expect(requestor.mock.calls[0]).toEqual([
        "POST",
        "/clients/1/experiments",
        params,
        success,
        error,
        true,
      ]);
    });

    it("supports (id)", () => {
      client.experimentCreate("1");
      expect(requestor.mock.calls[0]).toEqual([
        "POST",
        "/clients/1/experiments",
        {},
        null,
        null,
        true,
      ]);
    });

    it("supports (id, params)", () => {
      client.experimentCreate("1", params);
      expect(requestor.mock.calls[0]).toEqual([
        "POST",
        "/clients/1/experiments",
        params,
        null,
        null,
        true,
      ]);
    });

    it("supports (id, id2, success, error)", () => {
      client.observationsUpdate("1", "2", success, error);
      expect(requestor.mock.calls[0]).toEqual([
        "PUT",
        "/experiments/1/observations/2",
        {},
        success,
        error,
        true,
      ]);
    });

    it("supports (id, id2, success)", () => {
      client.observationsUpdate("1", "2", success);
      expect(requestor.mock.calls[0]).toEqual([
        "PUT",
        "/experiments/1/observations/2",
        {},
        success,
        null,
        true,
      ]);
    });

    it("supports (id, id2, params, success, error)", () => {
      client.observationsUpdate("1", "2", params, success, error);
      expect(requestor.mock.calls[0]).toEqual([
        "PUT",
        "/experiments/1/observations/2",
        params,
        success,
        error,
        true,
      ]);
    });

    it("supports integer arguments", () => {
      client.experimentCreate(1, success, error);
      expect(requestor.mock.calls[0]).toEqual([
        "POST",
        "/clients/1/experiments",
        {},
        success,
        error,
        true,
      ]);
    });

    it("supports null params", () => {
      client.experimentCreate("1", null, success, error);
      expect(requestor.mock.calls[0]).toEqual([
        "POST",
        "/clients/1/experiments",
        {},
        success,
        error,
        true,
      ]);
    });

    it("supports null success/error", () => {
      client.experimentCreate("1", params, null, null);
      expect(requestor.mock.calls[0]).toEqual([
        "POST",
        "/clients/1/experiments",
        params,
        null,
        null,
        true,
      ]);
    });

    it("disambiguates null success", () => {
      client.experimentCreate("1", params, null, error);
      expect(requestor.mock.calls[0]).toEqual([
        "POST",
        "/clients/1/experiments",
        params,
        null,
        error,
        true,
      ]);
    });

    it("disambiguates null params/success", () => {
      client.experimentCreate("1", null, null, error);
      expect(requestor.mock.calls[0]).toEqual([
        "POST",
        "/clients/1/experiments",
        {},
        null,
        error,
        true,
      ]);
    });

    it("errors on invalid calls", () => {
      const testInvalidCalls = (endpoint) => {
        const possibleIds = [[], ["1"], ["1", "2"]];
        _.each(possibleIds, (ids) => {
          expect(() => endpoint(...ids.concat([params, "abc"]))).toThrow();
          expect(() => endpoint(...ids.concat([params, params]))).toThrow();
          expect(() =>
            endpoint(...ids.concat([params, params, success, error])),
          ).toThrow();
          expect(() =>
            endpoint(...ids.concat([params, success, "abc"])),
          ).toThrow();
          expect(() =>
            endpoint(...ids.concat([success, error, "abc"])),
          ).toThrow();
          expect(() =>
            endpoint(...ids.concat([success, success, error])),
          ).toThrow();
          expect(() =>
            endpoint(...ids.concat([success, params, success, error])),
          ).toThrow();
        });
      };

      const testCallsWithZeroIds = (endpoint) => {
        expect(() => endpoint(null, success, error)).toThrow();
        expect(() => endpoint(params, success, error)).toThrow();
        expect(() => endpoint(success, error)).toThrow();
        expect(() => endpoint(success)).toThrow();
        expect(() => endpoint(params)).toThrow();
      };

      const testCallsWithOneId = (endpoint) => {
        expect(() => endpoint("1", null, success, error)).toThrow();
        expect(() => endpoint("1", params, success, error)).toThrow();
        expect(() => endpoint("1", success, error)).toThrow();
        expect(() => endpoint("1", success)).toThrow();
        expect(() => endpoint("1", params)).toThrow();
        expect(() => endpoint("1", params)).toThrow();
      };

      const testCallsWithTwoIds = (endpoint) => {
        expect(() => endpoint("1", "2", null, success, error)).toThrow();
        expect(() => endpoint("1", "2", params, success, error)).toThrow();
        expect(() => endpoint("1", "2", success, error)).toThrow();
        expect(() => endpoint("1", "2", success)).toThrow();
        expect(() => endpoint("1", "2", params)).toThrow();
      };

      testInvalidCalls(client.experimentCreate);
      testCallsWithZeroIds(client.experimentCreate);
      testCallsWithTwoIds(client.experimentCreate);

      testInvalidCalls(client.observationsUpdate);
      testCallsWithZeroIds(client.observationsUpdate);
      testCallsWithOneId(client.observationsUpdate);
    });
  });
});
