/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import LoggedInReactEndpoint from "../../../../server/endpoint/loggedin";
import Redirect from "../../../../net/redirect";

export default class ExperimentCreateEndpoint extends LoggedInReactEndpoint {
  get reactStrictMode() {
    return false;
  } // react-bootstrap-typeahead not supported
  pageName() {
    return "Create Experiment";
  }

  static page = require("./page");

  parseParams(req) {
    if (!req.loginState.clientId) {
      return Promise.reject(new Redirect("/user/info"));
    }
    return this.services.promiseApiClient
      .clients(req.loginState.clientId)
      .projects()
      .exhaustivelyPage()
      .then((projects) => ({
        alertBroker: req.services.alertBroker,
        legacyApiClient: req.services.legacyApiClient,
        clientId: req.loginState.clientId,
        errorNotifier: req.services.errorNotifier,
        isGuest: false,
        loginState: req.loginState,
        projects,
        promiseApiClient: req.services.promiseApiClient,
      }));
  }
}
