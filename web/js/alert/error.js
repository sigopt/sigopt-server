/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Alert from "./alert";

export default class NetError extends Alert {
  constructor(options) {
    super({
      message: options.message,
      type: "danger",
    });

    this.exception = options.exception;
    this.jqXhr = options.jqXhr;
    this.request = options.request;
    this.responseText = options.responseText;
    this.status = options.status || (this.jqXhr && this.jqXhr.status);
    this.tokenStatus = options.tokenStatus;
  }

  static constructFromAjaxResponse(jqXhr, request) {
    const responseText = jqXhr.responseText;
    let responseJson = null;

    try {
      responseJson = JSON.parse(responseText);
    } catch (err) {
      if (jqXhr.readyState === 0) {
        responseJson = {message: `Request failed: ${request.path}`};
      } else {
        responseJson = {message: jqXhr.statusText || "Server error"};
      }
    }

    return new NetError({
      exception: null,
      jqXhr: jqXhr,
      request: request,
      message: responseJson.message,
      responseText: responseText,
      tokenStatus: responseJson.token_status,
    });
  }
}
