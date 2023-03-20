/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import AppEndpoint from "../../server/endpoint/app";

export default class EmailVerifyEndpoint extends AppEndpoint {
  pageName() {
    return "Verify Email";
  }

  static page = require("./page");

  parseParams(req) {
    return Promise.resolve(this.renderPage(req));
  }

  renderPage(req) {
    return {
      alertBroker: this.services.alertBroker,
      code: req.query.code || req.body.code,
      email: req.query.email || req.body.email,
      legacyApiClient: this.services.legacyApiClient,
      loginState: req.loginState,
      navigator: this.services.navigator,
      promiseApiClient: this.services.promiseApiClient,
      sessionUpdater: this.services.sessionUpdater,
      status: 200,
    };
  }
}
