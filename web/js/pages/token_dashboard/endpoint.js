/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LoggedInReactEndpoint from "../../server/endpoint/loggedin";

export default class TokenDashboardEndpoint extends LoggedInReactEndpoint {
  pageName() {
    return "Token Dashboard";
  }

  static page = require("./page");

  parseParams(req) {
    const isGuest = req.apiTokenDetail.token_type === "guest";
    return Promise.all([
      this.getClient(req),
      this.getPermissions(req, isGuest),
    ]).then(([client, userPermissions]) => {
      const userPermission = _.find(
        userPermissions,
        (r) => r.client.id === req.loginState.clientId,
      );
      const hasSharePermission = userPermission
        ? userPermission.can_write
        : false;
      const sharingEnabled = req.configBroker.get("features.shareLinks", true);
      const canShare = hasSharePermission && sharingEnabled;
      return {
        alertBroker: this.services.alertBroker,
        canShare,
        client: client,
        loginState: req.loginState,
        promiseApiClient: this.services.promiseApiClient,
        sessionUpdater: this.services.sessionUpdater,
      };
    });
  }

  getClient(req) {
    if (req.matchedClient) {
      return Promise.resolve(req.matchedClient);
    } else if (req.loginState.clientId) {
      return this.services.promiseApiClient
        .clients(req.loginState.clientId)
        .fetch();
    } else {
      return Promise.resolve(null);
    }
  }

  getPermissions(req, isGuest) {
    if (isGuest) {
      return Promise.resolve(null);
    }
    return this.services.promiseApiClient
      .users(req.loginState.userId)
      .permissions()
      .exhaustivelyPage();
  }
}
