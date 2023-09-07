/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import btoa from "btoa";

import Service from "../services/base";
import SigoptError from "../error/base";
import {isDefinedAndNotNull, isUndefinedOrNull} from "../utils";

export const toAuthHeader = (token) => {
  const b64 = btoa(`${token}:`);
  return `Basic ${b64}`;
};

const UNSET = Symbol("UNSET");

export default class ApiRequestor extends Service {
  constructor(services, options, token = UNSET) {
    super(services, options);
    if (token === UNSET) {
      this._token = this.options.apiToken;
    } else {
      this._token = token;
    }
    if (process.env.NODE_DOMAIN === "server") {
      this.apiUrl = this.options.apiUrl;
    } else {
      const proxyUrl = this.options.externalAuthorizationEnabled
        ? null
        : this.options.clientApiUrl;
      this.apiUrl = proxyUrl || this.options.apiUrl;
    }
  }

  withApiToken(apiToken) {
    return new ApiRequestor(this._services, this._options, apiToken);
  }

  setApiToken(apiToken) {
    this._token = apiToken;
  }

  // NOTE: The legacy API client had baked in error notifying, which was brittle but
  // is hard to remove. So leave it as a hidden flag only used by LegacyApiClient. It should not
  // be used going forward
  request(
    method,
    path,
    unsanitizedParams,
    success,
    error,
    useLegacyErrorNotifier = false,
    urlPrefix = "/v1",
  ) {
    if (useLegacyErrorNotifier) {
      this.services.alertBroker.clearAlerts();
    }
    const params = this._sanitizeParams(method, unsanitizedParams);

    const host = this.apiUrl;

    const requestUrl = `${host}${urlPrefix}${path}`;

    const requestOptions = {
      method: method,
      url: requestUrl,
    };

    const token = this._token;
    requestOptions.headers = {
      "Content-Type": "application/json",
      "X-Trace-Id": this.options.traceId,
    };
    if (token) {
      requestOptions.headers.Authorization = toAuthHeader(token);
    }

    if (method === "GET" || method === "DELETE") {
      requestOptions.data = params;
    } else if (isDefinedAndNotNull(params)) {
      requestOptions.data = JSON.stringify(params);
    }

    const requestor = (errorHandler) =>
      this.services.netRequestor.request(
        requestOptions,
        success && this._wrapSuccess(success, errorHandler),
        errorHandler,
      );
    const errorHandler = (netError) => {
      // Because we still want to cleanup and report any unhandled errors,
      // we fall through after calling error, although we disable if the user explicitly
      // returns false from their error handler
      // eslint-disable-next-line callback-return
      const errorHandled = error && error(netError) === false;
      if (!errorHandled && useLegacyErrorNotifier) {
        this.services.errorNotifier.cleanupError(netError);
      }
    };
    const retryOn504 = (retries) =>
      requestor((netError) =>
        retries > 0 && method === "GET" && netError && netError.status === 504
          ? setTimeout(
              () => retryOn504(retries - 1),
              Math.floor(Math.random() * 500),
            )
          : errorHandler(netError),
      );
    return retryOn504(1);
  }

  _sanitizeParams(method, params) {
    return _.contains(["GET", "DELETE"], method)
      ? this._removeNullParams(params)
      : params;
  }

  _removeNullParams(params) {
    return _.omit(params, isUndefinedOrNull);
  }

  _wrapSuccess(success, error) {
    return function (data, status) {
      let parsed;
      try {
        parsed = JSON.parse(data);
      } catch (err) {
        return error(
          new SigoptError(
            `Invalid JSON response with status ${status}: ${data}`,
          ).chain(err),
        );
      }
      return success(parsed);
    };
  }

  serializeAs() {
    // NOTE: Don't send the traceId to the client - otherwise, all clientside API requests
    // will appear to have been part of the lifecycle of the initial web request.
    // TODO: Should we tie clientside requests to the initial web request that made them somehow?
    return _.extend({}, _.omit(this.options, "traceId"), {
      apiToken: this._token,
    });
  }
}
