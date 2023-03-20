/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import RedirectableEndpoint from "./redirectable";

export default class AppEndpoint extends RedirectableEndpoint {
  getApiTokens(req) {
    if (!req.loginState.clientId) {
      return Promise.resolve([null, null]);
    }
    return this.services.promiseApiClient
      .clients(req.loginState.clientId)
      .tokens()
      .exhaustivelyPage()
      .then((tokens) => {
        const eligibleTokens = _.filter(
          tokens,
          (t) =>
            t.client === req.loginState.clientId &&
            t.user === req.loginState.userId,
        );
        const [devTokens, apiTokens] = _.partition(
          eligibleTokens,
          (t) => t.development,
        );
        return [_.first(apiTokens), _.first(devTokens)];
      });
  }
}
