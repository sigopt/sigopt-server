/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import _validateCsrf from "../csrf";
import {BadParamError} from "../../../net/errors";

const validateCsrf = _validateCsrf();

describe("csrf", () => {
  const body = {csrf_token: "SOME_CSRF_TOKEN"};
  const csrfEndpoint = {shouldValidateCsrf: () => true};
  const noCsrfEndpoint = {shouldValidateCsrf: () => false};
  const validLoginState = {csrfToken: body.csrf_token};
  const invalidLoginState = {csrfToken: "WRONG_CSRF_TOKEN"};

  it("passes valid csrf tokens", () => {
    const request = {
      body,
      endpoint: csrfEndpoint,
      loginState: validLoginState,
      method: "POST",
    };
    validateCsrf(request, null, (val) => expect(val).toBeUndefined());
    expect(request.loginState).toEqual(validLoginState);
    expect(request.loginState.csrfToken).toBe("SOME_CSRF_TOKEN");
  });

  it("catches invalid csrf tokens", () => {
    const invalidLoginStateRequest = {
      body,
      endpoint: csrfEndpoint,
      loginState: invalidLoginState,
      method: "POST",
    };

    validateCsrf(invalidLoginStateRequest, null, (val) =>
      expect(val).toBeInstanceOf(BadParamError),
    );
    expect(invalidLoginStateRequest.loginState).not.toEqual(invalidLoginState);
    expect(invalidLoginStateRequest.loginState.csrfToken).toBeUndefined();

    const invalidBodyRequest = {
      body: {},
      endpoint: csrfEndpoint,
      loginState: validLoginState,
      method: "POST",
    };
    validateCsrf(invalidBodyRequest, null, (val) =>
      expect(val).toBeInstanceOf(BadParamError),
    );
    expect(invalidLoginStateRequest.loginState).not.toEqual(validLoginState);
    expect(invalidBodyRequest.loginState.csrfToken).toBeUndefined();
  });

  it("only checks POST requests", () => {
    _.each(["GET", "HEAD", "PUT", "OPTIONS"], (method) => {
      const request = {
        body,
        endpoint: csrfEndpoint,
        loginState: invalidLoginState,
        method,
      };
      validateCsrf(request, null, (val) => expect(val).toBeUndefined());
      expect(request.loginState).toBe(invalidLoginState);
    });
  });

  it("skips no csrf endpoints", () => {
    const request = {
      body,
      endpoint: noCsrfEndpoint,
      loginState: invalidLoginState,
      method: "POST",
    };
    validateCsrf(request, null, (val) => expect(val).toBeUndefined());
    expect(request.loginState).toBe(invalidLoginState);
  });
});
