/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import LoggedInReactEndpoint from "../../../server/endpoint/loggedin";

export default class UserDeleteEndpoint extends LoggedInReactEndpoint {
  pageName() {
    return "Delete Account";
  }

  static page = require("./page");

  parseParams(req) {
    return this.services.promiseApiClient
      .users(req.loginState.userId)
      .permissions()
      .exhaustivelyPage()
      .then((userPermissions) => ({
        alertBroker: req.services.alertBroker,
        loginState: req.loginState,
        promiseApiClient: req.services.promiseApiClient,
        navigator: req.services.navigator,
        sessionUpdater: req.services.sessionUpdater,
        userPermissions: userPermissions,
      }));
  }
}
