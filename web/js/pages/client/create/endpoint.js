/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import LoggedInReactEndpoint from "../../../server/endpoint/loggedin";

export default class ClientCreateEndpoint extends LoggedInReactEndpoint {
  static page = require("./page");
  parseParams(req) {
    return Promise.resolve({
      alertBroker: this.services.alertBroker,
      loginState: req.loginState,
      navigator: this.services.navigator,
      promiseApiClient: this.services.promiseApiClient,
      sessionUpdater: this.services.sessionUpdater,
    });
  }
}
