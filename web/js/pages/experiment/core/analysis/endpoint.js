/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ExperimentEndpoint from "../../server/endpoint";

export default class ExperimentAnalysisEndpoint extends ExperimentEndpoint {
  pageName() {
    return "Analysis";
  }
  get reactStrictMode() {
    return false;
  } // react-select not supported

  static page = require("../../common/analysis/page");

  parseParams(req) {
    return req.services.promiseApiClient
      .experiments(req.matchedExperiment.id)
      .metricImportances()
      .exhaustivelyPage()
      .catch((e) =>
        e.status === 422 ? Promise.resolve(null) : Promise.reject(e),
      )
      .then((metricImportances) =>
        Promise.resolve({
          alertBroker: req.services.alertBroker,
          experiment: req.matchedExperiment,
          metricImportances: metricImportances,
          promiseApiClient: req.services.promiseApiClient,
        }),
      );
  }
}
