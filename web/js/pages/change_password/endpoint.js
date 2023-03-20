/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import AppEndpoint from "../../server/endpoint/app";
import Redirect from "../../net/redirect";
import validateContinueHref from "../../net/continue";

export default class ChangePasswordEndpoint extends AppEndpoint {
  pageName() {
    return "Change Password";
  }

  static page = require("./page");

  parseParams(req) {
    const code = req.query.code;
    if (!code && !req.currentUser) {
      return Promise.reject(new Redirect("/user/info"));
    }
    return Promise.resolve({
      alertBroker: this.services.alertBroker,
      canReset: req.configBroker.get("email.enabled"),
      code: code,
      continueHref: validateContinueHref(req.query.continue, req.configBroker),
      email: req.query.email,
      loginState: req.loginState,
      navigator: this.services.navigator,
      promiseApiClient: this.services.promiseApiClient,
      required: Boolean(req.query.required),
      sessionUpdater: this.services.sessionUpdater,
      user: req.currentUser,
    });
  }
}
