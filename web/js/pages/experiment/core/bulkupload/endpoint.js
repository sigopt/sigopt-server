/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ExperimentEndpoint from "../../server/endpoint";

export default class ExperimentReportEndpoint extends ExperimentEndpoint {
  pageName() {
    return "Bulk Data Entry";
  }

  static page = require("./page");

  parseParams(req) {
    const params = {
      alertBroker: req.services.alertBroker,
      ajaxClient: req.services.ajaxClient,
      batchSize: req.configBroker.get(
        "features.maxObservationsCreateCount",
        2500,
      ),
    };
    return Promise.resolve(params);
  }
}
