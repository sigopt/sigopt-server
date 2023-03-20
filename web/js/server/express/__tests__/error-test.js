/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import DefaultResponseSerializer from "../../serializer/default";
import ErrorEndpoint from "../../../pages/error/endpoint";
import LoginEndpoint from "../../../pages/landing/login/endpoint";
import {
  BadParamError,
  NotFoundError,
  PromptForLoginError,
  RequestError,
  SicknessError,
} from "../../../net/errors";
import {errorHandler} from "../error";

jest.mock("../../serializer/default");

describe("handleErrors", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    DefaultResponseSerializer.mockImplementation(function () {
      this.getSerializedBody = () => "serialized body";
    });
    jest.spyOn(console, "error").mockImplementation(_.noop);
  });

  const globalServices = {
    configBroker: {
      get: (name, defaultValue) => defaultValue,
    },
  };

  const loginState = {userId: "123"};

  const logger = {
    error: jest.fn(/* console.error */),
  };

  const req = {
    body: {},
    configBroker: globalServices.configBroker,
    loginState: loginState,
    path: "/experiments",
    query: {},
    services: {
      logger: logger,
    },
  };

  const res = {
    send: jest.fn(),
    status: jest.fn(),
  };

  describe("error responses", () => {
    const handleError = (err) => errorHandler(err, req, res, globalServices);

    _.each(
      [
        Error,
        RequestError,
        BadParamError,
        NotFoundError,
        SicknessError,
        PromptForLoginError,
      ],
      (ErrorClass) => {
        it(`sends an error response for ${ErrorClass}`, () => {
          const err = new ErrorClass();
          return handleError(err).then((response) => {
            expect(response).not.toEqual(expect.anything());
            expect(res.send.mock.calls).toEqual([
              [expect.stringContaining("serialized body")],
            ]);
            expect(res.status).toHaveBeenCalledTimes(1);
            expect(logger.error.mock.calls).toEqual([
              ["sigopt.www.apiexception", err],
            ]);
          });
        });
      },
    );

    _.each(
      [Error, RequestError, BadParamError, NotFoundError, SicknessError],
      (ErrorClass) => {
        it(`shows error page on ${ErrorClass}`, () => {
          const err = new ErrorClass();
          return handleError(err).then(() => {
            expect(req.endpoint).toBeInstanceOf(ErrorEndpoint);
          });
        });
      },
    );

    it("shows login page on PromptForLoginError", () => {
      const err = new PromptForLoginError();
      return handleError(err).then(() => {
        expect(req.endpoint).toBeInstanceOf(LoginEndpoint);
      });
    });

    _.each(
      [
        [Error, 500],
        [BadParamError, 400],
        [NotFoundError, 404],
        [RequestError, 500],
        [SicknessError, 500],
        [PromptForLoginError, 404],
      ],
      ([ErrorClass, status]) => {
        it(`sets the error to ${status} for ${ErrorClass}`, () => {
          const err = new ErrorClass();
          return handleError(err).then(() => {
            expect(res.status.mock.calls).toEqual([[status]]);
          });
        });
      },
    );

    _.each(
      [Error, BadParamError, RequestError, NotFoundError, PromptForLoginError],
      (ErrorClass) => {
        it("doesnt show test error prompt for users", () => {
          const err = new ErrorClass();
          return handleError(err).then(() => {
            expect(req.endpointParams.showTestError).toBeFalsy();
          });
        });
      },
    );

    it("shows test error prompt on sickness page", () => {
      const err = new SicknessError();
      return handleError(err).then(() => {
        expect(req.endpointParams.showTestError).toBeTruthy();
      });
    });
  });

  describe("robustness to subsequent errors", () => {
    it("handles errors before req.services is set", () => {
      const err = new Error("My custom error");
      const ourReq = _.extend({}, req, {services: undefined});
      return errorHandler(err, ourReq, res, globalServices).then((response) => {
        expect(err.showNeedsLogin).toBeFalsy();
        expect(response).not.toEqual(expect.anything());
        expect(ourReq.endpoint).toBeInstanceOf(ErrorEndpoint);
        expect(res.send.mock.calls).toEqual([
          [expect.stringContaining("serialized body")],
        ]);
        expect(res.status.mock.calls).toEqual([[500]]);
        expect(logger.error.mock.calls).toEqual([]);
      });
    });

    it("handles errors thrown by the error page", () => {
      // If there's an error in the error page, make sure that's the one we logged.
      // This means the user will get a blank 500 page, but really there's nothing else
      // we can show since we've already demonstrated our inability to show an error page
      const err = new Error("My custom error");
      const renderingError = new Error("my rendering error");
      DefaultResponseSerializer.mockImplementation(function () {
        this.getSerializedBody = () => {
          throw renderingError;
        };
      });
      return errorHandler(err, req, res, globalServices).then((response) => {
        expect(response).not.toEqual(expect.anything());
        expect(logger.error.mock.calls).toEqual([
          ["sigopt.www.apiexception", err],
          ["sigopt.www.apiexception", renderingError],
        ]);
      });
    });

    it("handles errors in express response writing", () => {
      // If something upstream starts writing the response early, then it is possible that
      // calling `res.status` will fail (since it is too late to send the response status).
      // In this case, make sure that the res.write error was logged
      const err = new Error("My custom error");
      const responseError = new Error("my response error");
      const failedWrite = jest.fn(() => {
        throw responseError;
      });
      return errorHandler(
        err,
        req,
        _.extend({}, res, {send: failedWrite}),
        globalServices,
      ).then((response) => {
        expect(response).not.toEqual(expect.anything());
        expect(logger.error.mock.calls).toEqual([
          ["sigopt.www.apiexception", err],
          ["sigopt.www.apiexception", responseError],
        ]);
      });
    });
  });
});
