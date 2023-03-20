/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ExperimentEndpoint from "../../server/endpoint";

export default class ExperimentSuggestionsEndpoint extends ExperimentEndpoint {
  pageName() {
    return "Suggestions";
  }

  static page = require("./page");

  parseParams(req) {
    return Promise.resolve({
      alertBroker: req.services.alertBroker,
      loginState: req.loginState,
    });
  }
}
