/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ExperimentListEndpoint from "../../experiment/list/endpoint";

export default class AiExperimentListEndpoint extends ExperimentListEndpoint {
  pageName() {
    return "AI Experiments";
  }

  parseParams(req) {
    return Promise.resolve(super.parseParams(req)).then((params) => ({
      ...params,
      isAiExperiment: true,
    }));
  }

  _getListEndpoint(clientId) {
    return this.services.promiseApiClient.clients(clientId).aiexperiments();
  }

  _extendListParams(params) {
    return params;
  }
}
