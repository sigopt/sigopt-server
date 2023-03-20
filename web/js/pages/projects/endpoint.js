/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LoggedInReactEndpoint from "../../server/endpoint/loggedin";
import Redirect from "../../net/redirect";

export default class ProjectsEndpoint extends LoggedInReactEndpoint {
  pageName() {
    return "AI Projects";
  }

  static page = require("./page");

  parseParams(req) {
    if (!req.loginState.clientId) {
      return Promise.reject(new Redirect("/user/info"));
    }
    const pageParams = _.pick(req.query, "includeClient", "page");
    return Promise.all([
      this._fetchClient(req.loginState.clientId),
      this.services.promiseApiClient
        .users(req.loginState.userId)
        .permissions()
        .exhaustivelyPage(),
    ]).then(([client, userPermissions]) => {
      const currentPermission = _.find(
        userPermissions,
        (r) => client && r.client.id === client.id,
      );
      return {
        alertBroker: req.services.alertBroker,
        currentPermission: currentPermission,
        currentUser: req.currentUser,
        legacyApiClient: req.services.legacyApiClient,
        loginState: req.loginState,
        pageParams: pageParams,
        promiseApiClient: req.services.promiseApiClient,
      };
    });
  }

  _fetchClient(clientId) {
    if (clientId) {
      return this.services.promiseApiClient.clients(clientId).fetch();
    } else {
      return Promise.resolve(null);
    }
  }
}
