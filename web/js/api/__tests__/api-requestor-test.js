/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import ApiRequestor, {toAuthHeader} from "../api-requestor";

jest.useFakeTimers();

function fail() {
  throw new Error("FAIL");
}

const API_TOKEN = "API_TOKEN";

describe("ApiRequestor", () => {
  const makeApiRequestor = (onRequest, onErrorCleanup) =>
    new ApiRequestor(
      {
        alertBroker: {clearAlerts: _.noop},
        errorNotifier: {cleanupError: onErrorCleanup || fail},
        netRequestor: {request: onRequest || fail},
      },
      {apiToken: API_TOKEN},
    );

  const error400 = {status: 400};
  const error504 = {status: 504};

  it("makes one request when successful", () => {
    const requestFn = jest.fn((options, success) => success("{}"));
    const apiRequestor = makeApiRequestor(requestFn, fail);
    apiRequestor.request("GET", "/", {}, _.noop, fail);
    jest.runAllTimers();
    expect(requestFn.mock.calls).toHaveLength(1);
    expect(requestFn.mock.calls[0][0].headers.Authorization).toEqual(
      toAuthHeader(API_TOKEN),
    );
  });

  it("allows overriding API token", () => {
    const requestFn = jest.fn((options, success) => success("{}"));
    const apiRequestor = makeApiRequestor(requestFn, fail);
    apiRequestor
      .withApiToken("OTHER_TOKEN")
      .request("GET", "/", {}, _.noop, fail);
    apiRequestor.request("GET", "/", {}, _.noop, fail);
    expect(requestFn.mock.calls).toHaveLength(2);
    expect(requestFn.mock.calls[0][0].headers.Authorization).toEqual(
      toAuthHeader("OTHER_TOKEN"),
    );
    expect(requestFn.mock.calls[1][0].headers.Authorization).toEqual(
      toAuthHeader(API_TOKEN),
    );
  });

  it("calls success once", () => {
    const successFn = jest.fn();
    const apiRequestor = makeApiRequestor(
      (options, success) => success("{}"),
      fail,
    );
    apiRequestor.request("GET", "/", {}, successFn, fail);
    jest.runAllTimers();
    expect(successFn.mock.calls).toHaveLength(1);
  });

  it("makes one request with null errors", () => {
    const requestFn = jest.fn((options, success, error) => error(null));
    const apiRequestor = makeApiRequestor(requestFn, fail);
    apiRequestor.request("GET", "/", {}, fail, _.noop);
    jest.runAllTimers();
    expect(requestFn.mock.calls).toHaveLength(1);
  });

  it("makes one request with unknown errors", () => {
    const requestFn = jest.fn((options, success, error) => error(error400));
    const apiRequestor = makeApiRequestor(requestFn, fail);
    apiRequestor.request("GET", "/", {}, fail, _.noop);
    jest.runAllTimers();
    expect(requestFn.mock.calls).toHaveLength(1);
  });

  it("uses legacy error handling", () => {
    const cleanupFn = jest.fn();
    const apiRequestor = makeApiRequestor(
      (options, success, error) => error(error400),
      cleanupFn,
    );
    apiRequestor.request("GET", "/", {}, fail, _.noop, true);
    jest.runAllTimers();
    expect(cleanupFn.mock.calls).toHaveLength(1);
  });

  it("legacy error handling skipped on false", () => {
    const requestFn = jest.fn((options, success, error) => error(error400));
    const apiRequestor = makeApiRequestor(requestFn, fail);
    apiRequestor.request("GET", "/", {}, fail, () => false, true);
    jest.runAllTimers();
    expect(requestFn.mock.calls).toHaveLength(1);
  });

  it("retries on 504 GET errors", () => {
    const requestFn = jest
      .fn(fail)
      .mockImplementationOnce((options, success, error) => error(error504))
      .mockImplementationOnce((options, success) => success("{}"));
    const apiRequestor = makeApiRequestor(requestFn, fail);
    apiRequestor.request("GET", "/", {}, _.noop, _.noop);
    jest.runAllTimers();
    expect(requestFn.mock.calls).toHaveLength(2);
  });

  _.each(["POST", "PUT", "DELETE"], (method) =>
    it(`does not retry 504 ${method} errors`, () => {
      const requestFn = jest
        .fn(fail)
        .mockImplementationOnce((options, success, error) => error(error504));
      const apiRequestor = makeApiRequestor(requestFn, fail);
      apiRequestor.request(method, "/", {}, _.noop, _.noop);
      jest.runAllTimers();
      expect(requestFn.mock.calls).toHaveLength(1);
    }),
  );
});
