/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import ExperimentEndpoint from "../../server/endpoint";

export default class ExperimentApiEndpoint extends ExperimentEndpoint {
  pageName() {
    return "API";
  }

  static page = require("../../common/api/page");

  parseParams(req) {
    const pageParams = _.pick(req.query, "language");

    return Promise.all([this._fetchClientTokens(req.loginState.clientId)]).then(
      ([clientTokens]) => {
        const clientToken = _.find(
          clientTokens,
          (t) => !t.development && t.user === req.loginState.userId,
        );
        return {
          apiToken: clientToken && clientToken.token,
          apiUrl: req.configBroker.get("address.api_url"),
          appUrl: req.configBroker.get("address.app_url"),
          loginState: req.loginState,
          pageParams: _.all(pageParams, _.identity) && pageParams,
        };
      },
    );
  }

  _fetchClientTokens(clientId) {
    if (clientId) {
      return this.services.promiseApiClient
        .clients(clientId)
        .tokens()
        .exhaustivelyPage();
    } else {
      return Promise.resolve([]);
    }
  }
}
