/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import AppEndpoint from "../../server/endpoint/app";
import {PromptForLoginError} from "../../net/errors";

export default class SetupEndpoint extends AppEndpoint {
  pageName() {
    return "Set Up Your Account";
  }

  static page = require("./page");

  parseParams(req) {
    if (req.loginState.userId) {
      return Promise.resolve(this.renderPage(req));
    } else {
      return Promise.reject(new PromptForLoginError());
    }
  }

  renderPage(req) {
    return {
      loginState: req.loginState,
      navigator: this.services.navigator,
      promiseApiClient: this.services.promiseApiClient,
    };
  }
}
