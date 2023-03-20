/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ExperimentEndpoint from "../../server/endpoint";

export default class ExperimentHistoryEndpoint extends ExperimentEndpoint {
  pageName() {
    return "History";
  }

  static page = require("../../common/history/page");

  parseParams(req) {
    return this._fetchClient(req.matchedExperiment.client).then((client) => {
      return Promise.resolve({
        alertBroker: req.services.alertBroker,
        client,
        loginState: req.loginState,
      });
    });
  }
}
