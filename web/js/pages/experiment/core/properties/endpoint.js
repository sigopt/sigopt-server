/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ExperimentEndpoint from "../../server/endpoint";

export default class ExperimentPropertiesEndpoint extends ExperimentEndpoint {
  get reactStrictMode() {
    return false;
  } // react-bootstrap-typeahead not supported
  pageName() {
    return "Properties";
  }

  static page = require("../../common/properties/page");

  parseParams(req) {
    return this._fetchCreator(req.matchedExperiment).then((creator) => ({
      alertBroker: req.services.alertBroker,
      clientId: req.matchedExperiment.client,
      creator: creator,
      errorNotifier: req.services.errorNotifier,
      loginState: req.loginState,
      promiseApiClient: req.services.promiseApiClient,
    }));
  }
}
