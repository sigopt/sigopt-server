/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import AppEndpoint from "../../server/endpoint/app";

export default class ForgotPasswordEndpoint extends AppEndpoint {
  pageName() {
    return "Forgot Password";
  }
  static page = require("./page");

  parseParams(req) {
    return Promise.resolve({
      alertBroker: this.services.alertBroker,
      legacyApiClient: this.services.legacyApiClient,
      canReset: req.configBroker.get("email.enabled"),
      loginState: req.loginState,
    });
  }
}
