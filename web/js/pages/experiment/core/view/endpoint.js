/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ExperimentEndpoint from "../../server/endpoint";

export default class ExperimentViewEndpoint extends ExperimentEndpoint {
  pageName() {
    return "Summary";
  }

  static page = require("../../common/view/page");

  parseParams(req) {
    return Promise.resolve({
      alertBroker: req.services.alertBroker,
      errorNotifier: req.services.errorNotifier,
      legacyApiClient: req.services.legacyApiClient,
      promiseApiClient: req.services.promiseApiClient,
    });
  }
}
