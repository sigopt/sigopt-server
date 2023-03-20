/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LoggedInReactEndpoint from "../../server/endpoint/loggedin";

export default class TokenInfoEndpoint extends LoggedInReactEndpoint {
  pageName() {
    return "API Tokens";
  }

  static page = require("./page");

  parseParams(req) {
    return this._fetchClientInfo(req.loginState.clientId).then(
      ([client, clientTokens]) => {
        const clientToken = _.find(
          clientTokens,
          (t) => !t.development && t.user === req.loginState.userId,
        );
        const devToken = _.find(
          clientTokens,
          (t) => t.development && t.user === req.loginState.userId,
        );
        const emailVerificationEnabled = req.configBroker.get("email.verify");
        return {
          ajaxClient: this.services.ajaxClient,
          alertBroker: this.services.alertBroker,
          legacyApiClient: this.services.legacyApiClient,
          client: client,
          clientToken: clientToken,
          currentUserPermissions: req.currentUserPermissions,
          developmentToken: devToken && devToken.token,
          loginState: req.loginState,
          shouldVerifyEmail:
            emailVerificationEnabled && !req.currentUser.has_verified_email,
          user: req.currentUser,
        };
      },
    );
  }

  _fetchClientInfo(clientId) {
    return this._fetchClient(clientId)
      .catch((e) => (e.status === 404 ? null : Promise.reject(e)))
      .then((client) =>
        Promise.all([client, client && this._fetchClientTokens(client.id)]),
      );
  }

  _fetchClient(clientId) {
    if (clientId) {
      return this.services.promiseApiClient.clients(clientId).fetch();
    } else {
      return Promise.resolve(null);
    }
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
