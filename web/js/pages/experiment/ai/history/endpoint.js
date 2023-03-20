/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ExperimentEndpoint from "../../server/endpoint";

export default class AiExperimentHistoryEndpoint extends ExperimentEndpoint {
  pageName() {
    return "History";
  }

  static page = require("../../common/history/page");

  parseParams(req) {
    return Promise.all([
      this._fetchClient(req.matchedExperiment.client),
      this._fetchProject(req.matchedExperiment),
    ]).then(([client, project]) => {
      return Promise.resolve({
        alertBroker: req.services.alertBroker,
        client,
        isAiExperiment: true,
        loginState: req.loginState,
        project,
      });
    });
  }
}
