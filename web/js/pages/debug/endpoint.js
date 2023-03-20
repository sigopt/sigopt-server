/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import ReactEndpoint from "../../server/endpoint/react";

export default class DebugEndpoint extends ReactEndpoint {
  pageName() {
    return "Debug Page";
  }

  static page = require("./page");

  parseParams(req) {
    return Promise.resolve({
      ajaxClient: this.services.ajaxClient,
      legacyApiClient: this.services.legacyApiClient,
      headers: _.omit(req.headers, "cookie", "host"),
      loginState: req.loginState,
    });
  }
}
